"""Meaningful invariants for the model, FL oracle and both optimizer implementations."""
import copy
import unittest
from types import SimpleNamespace
import numpy as np
import torch
from uavfl.config import load_config
from uavfl.physics import Scenario, Genome
from uavfl.metrics import dominates, nondominated_indices, hypervolume3
from uavfl.learning import CNN, Reference, initial_checkpoint
from uavfl.data import DataBundle
from uavfl.operators import initialize, HistoricalGuide, HistoryReport
from uavfl.optimizers import run_optimizer, weight_vectors, tchebycheff, Candidate, fronts, crowding

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.cfg=load_config();self.scenario=Scenario(self.cfg)
        self.g=Genome(np.array([1,1,0,2,0,0]),np.ones(6),0.5)

    def test_exact_ledger_and_timeline(self):
        p=self.scenario.evaluate(self.g)
        self.assertTrue(p.feasible)
        expected=sum(p.phases[k] for k in ("D0","D","service","A","H","A0"))
        self.assertAlmostEqual(p.duration,expected)
        self.assertAlmostEqual(p.energy,sum(p.ledger["clients"])+sum(p.ledger["uavs"])+p.ledger["coordinator"])
        for kind in ("client","uav"):
            parts=p.ledger[kind+"_parts"]
            np.testing.assert_allclose(np.sum(list(parts.values()),axis=0),p.ledger["clients" if kind=="client" else "uavs"])
        np.testing.assert_allclose(p.ledger["client_parts"]["compute"][2],0)
        self.assertGreater(p.ledger["client_parts"]["base"][2],0)

    def test_empty_uav_still_hovers(self):
        g=Genome(np.array([1,0,0,0,0,0]),np.ones(6),.5)
        p=self.scenario.evaluate(g)
        self.assertGreater(p.ledger["uavs"][1],0)
        self.assertEqual(p.phases["Hu"][1],0)
        self.assertEqual(p.phases["Au"][1],0)

    def test_cpu_reduction_preserves_service(self):
        rng=np.random.default_rng(9)
        for g in initialize(self.scenario,25,19):
            f=np.where(g.assignment>0,rng.uniform(.5e9,2e9,6),0)
            original=self.scenario.evaluate(g,frequencies=f)
            ph=original.phases
            xi=(ph["service"]-ph["dmin"])/(ph["dcap"]-ph["dmin"])
            if 0<=xi<=1:
                gg=g.copy();gg.xi=float(xi)
                reduced=self.scenario.evaluate(gg)
                self.assertAlmostEqual(reduced.duration,original.duration,places=9)
                self.assertLessEqual(reduced.energy,original.energy+1e-8)
                self.assertTrue(np.all(reduced.frequency<=f+1))

    def test_bandwidth_and_mask(self):
        p=self.scenario.evaluate(self.g)
        self.assertAlmostEqual(p.bandwidth[:2].sum(),2e6)
        self.assertAlmostEqual(p.bandwidth[3],2e6)
        self.assertTrue(np.all(p.bandwidth[self.g.assignment==0]==0))
        rate1=self.scenario.rate(0,0,1e5);rate2=self.scenario.rate(0,0,2e5)
        self.assertGreater(rate2,rate1)
        with self.assertRaises(ValueError):self.scenario.rate(0,0,0)

    def test_deadline_battery_and_nonfinite(self):
        tight=copy.deepcopy(self.cfg);tight["network"]["deadline"]=.01
        p=Scenario(tight).evaluate(self.g)
        self.assertFalse(p.feasible);self.assertGreater(p.cv,0)
        scenario=Scenario(self.cfg);scenario.uav_battery[:]=scenario.n["uav_reserve"]
        self.assertFalse(scenario.evaluate(self.g).feasible)
        bad=self.g.copy();bad.xi=float("nan")
        with self.assertRaises(ValueError):self.scenario.evaluate(bad)
        empty=Genome(np.zeros(6,int),np.ones(6),.5)
        self.assertFalse(self.scenario.evaluate(empty).feasible)

class MetricTests(unittest.TestCase):
    def test_exact_hypervolume(self):
        self.assertAlmostEqual(hypervolume3([[1,1,1]],[2,2,2]),1)
        self.assertAlmostEqual(hypervolume3([[1,1,1],[.5,1.5,1.5]],[2,2,2]),1.125)
        self.assertAlmostEqual(hypervolume3([[1,1,1],[1,1,1],[3,0,0]],[2,2,2]),1)
        self.assertEqual(hypervolume3([], [2,2,2]),0)

    def test_nondominance(self):
        y=np.array([[1,3,2],[2,2,2],[3,3,3],[.5,4,1]])
        self.assertEqual(set(nondominated_indices(y)),{0,1,3})
        self.assertFalse(dominates(y[0],y[0]))

    def test_weights_and_scalarization(self):
        for n in (4,10,28,64):
            w=weight_vectors(n)
            self.assertEqual(w.shape,(n,3));np.testing.assert_allclose(w.sum(1),1)
            self.assertTrue((w>=0).all())
        self.assertAlmostEqual(tchebycheff(np.array([1,2,3]),np.array([.2,.3,.5]),np.zeros(3),np.ones(3)),1.5)

    def test_zero_range_crowding_and_constraints(self):
        def c(y,feasible=True,cv=0):
            return Candidate(None,SimpleNamespace(feasible=feasible,cv=cv),np.array(y) if feasible else None,0,())
        pop=[c([1,1,1]),c([1,1,1]),c(None,False,.2),c(None,False,.5)]
        self.assertEqual(fronts(pop),[[0,1],[2],[3]])
        self.assertEqual(crowding(pop,[0,1]),{0:0,1:0})

class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.cfg=load_config();cls.cfg["fl"].update(local_steps=1,batch_size=4,search_replicates=2,audit_replicates=2)
        gen=torch.Generator().manual_seed(5)
        data={}
        for split in ("train","search","audit","test"):
            data[split]=[(torch.rand(8,1,28,28,generator=gen),torch.randint(10,(8,),generator=gen)) for _ in range(3)]
        cls.bundle=DataBundle(data,np.array([.2,.3,.5]),"unit-data",{})
        cls.checkpoint=initial_checkpoint(55)

    def test_guided_swap_keeps_unknown_clients(self):
        cfg=load_config();scenario=Scenario(cfg);model=np.zeros(5)
        reports={i:HistoryReport(np.array([value,0.]),0,model)
                 for i,value in enumerate([4.,-2.,0.])}
        guide=HistoricalGuide(np.ones(6)/6,reports,model,1,cfg['search'])
        g=Genome(np.array([1,0,0,2,0,0]),np.ones(6),.5)
        child=guide.swap(g,scenario,np.random.default_rng(7),16)
        self.assertIsNotNone(child)
        self.assertEqual(child.assignment[3],2)
        self.assertEqual(child.assignment[0],0)
        self.assertNotEqual(child.assignment[2],0)
        self.assertLess(guide.score(np.flatnonzero(child.assignment)),guide.score([0,3]))
    def test_model_count_and_cache_determinism(self):
        self.assertEqual(sum(p.numel() for p in CNN().parameters()),105866)
        ref=Reference(self.bundle,self.checkpoint,self.cfg,5)
        before=ref.checkpoint()
        a=ref.loss((0,2));b=ref.loss((2,0))
        self.assertEqual(a,b)
        self.assertEqual(ref.stats["search"]["set_misses"],1)
        self.assertEqual(ref.stats["search"]["set_hits"],1)
        torch.testing.assert_close(before,ref.checkpoint(),rtol=0,atol=0)
        ref2=Reference(self.bundle,self.checkpoint,self.cfg,5)
        self.assertEqual(a,ref2.loss((0,2)))

    def test_audit_namespace_and_hierarchical_aggregation(self):
        ref=Reference(self.bundle,self.checkpoint,self.cfg,5)
        flat=ref.aggregate((0,1,2),"search",0)
        d=[ref._update(i,"search",0) for i in range(3)]
        first=(.2*d[0]+.3*d[1])/.5
        hierarchical=self.checkpoint+.5*first+.5*d[2]
        torch.testing.assert_close(flat,hierarchical,rtol=1e-5,atol=1e-7)
        before=copy.deepcopy(dict(ref.stats["search"]))
        ref.loss((0,1),"audit")
        self.assertEqual(ref.stats["search"],before)
        self.assertNotEqual(ref.namespace,Reference(self.bundle,self.checkpoint+.01,self.cfg,5).namespace)

    def test_guide_missing_stale_and_unequal_weights(self):
        model=np.zeros(5)
        reports={0:HistoryReport(np.array([2.,0.]),0,model),1:HistoryReport(np.array([-1.,0.]),0,model),
                 2:HistoryReport(np.array([3.,0.]),-100,model)}
        settings=load_config()["search"]
        guide=HistoricalGuide([.2,.3,.5],reports,model,1,settings)
        self.assertEqual(set(guide.reports),{0,1})
        self.assertAlmostEqual(guide.coverage,.5)
        self.assertIsNone(guide.score([2]))
        self.assertAlmostEqual(guide.score([0,1]),0)
        self.assertGreater(guide.score([0]),0)

class OptimizerTests(unittest.TestCase):
    def test_both_algorithms_and_locked_budget(self):
        cfg=load_config();cfg["search"].update(population=10,seconds=10,max_proposals=40,trace_seconds=100)
        scenario=Scenario(cfg);initial=initialize(scenario,10,1)
        class DummyReference:
            def __init__(self):
                self.stats={"search":{"set_misses":0,"set_hits":0,"update_misses":0,"update_hits":0,"seconds":0}}
                self.cache={}
            def loss(self,selected,phase):
                if selected not in self.cache:
                    self.cache[selected]=2.4-.04*len(selected)+.003*sum(selected)
                    self.stats["search"]["set_misses"]+=1
                else:self.stats["search"]["set_hits"]+=1
                return {"mean":self.cache[selected],"replicates":[self.cache[selected]]}
        for name in ("nsga2","moead"):
            ev,stats=run_optimizer(name,initial,scenario,DummyReference(),cfg["search"],42)
            self.assertEqual(stats["proposals"],40)
            self.assertTrue(ev.archive)
            for c in ev.archive:
                self.assertTrue(c.physical.feasible)
                self.assertFalse(any(dominates(x.objectives,c.objectives) for x in ev.archive))
            self.assertTrue(all(np.array_equal(g.assignment,c["assignment"])
                for g,c in zip(initial,ev.records[:10])))

if __name__=="__main__":unittest.main()
