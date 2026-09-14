"""Unit tests for DAG-informed BKT experimental variants and strategy boundaries."""
import networkx as nx
import pytest

from ace.learner.bkt import BKTModel, BKTParameters
from ace.learner.dag_bkt import BKTStrategy, DAGConditionedBKT


@pytest.mark.unit
def test_dag_bkt_baseline_strategy_unaltered():
    graph = nx.DiGraph()
    graph.add_edge("skill_a", "skill_b")  # A -> B

    bkt_model = BKTModel(BKTParameters(p_l0=0.20))
    dag_bkt = DAGConditionedBKT(graph=graph, bkt_model=bkt_model, strategy=BKTStrategy.BASELINE)

    # In BASELINE strategy, parent mastery does not alter prior P(L0)
    prior_zero = dag_bkt.get_conditioned_prior("skill_b", learner_masteries={"skill_a": 0.0})
    prior_full = dag_bkt.get_conditioned_prior("skill_b", learner_masteries={"skill_a": 1.0})

    assert prior_zero == 0.20
    assert prior_full == 0.20


@pytest.mark.unit
def test_dag_bkt_dag_prior_strategy_modulation():
    graph = nx.DiGraph()
    graph.add_edge("skill_a", "skill_b")

    bkt_model = BKTModel(BKTParameters(p_l0=0.20))
    dag_bkt = DAGConditionedBKT(graph=graph, bkt_model=bkt_model, strategy=BKTStrategy.DAG_PRIOR)

    # Parent A unmastered (0.0): prior drops
    prior_zero = dag_bkt.get_conditioned_prior("skill_b", learner_masteries={"skill_a": 0.0})
    assert prior_zero < 0.20
    assert prior_zero == round(0.20 * 0.20, 4)

    # Parent A fully mastered (1.0): prior remains near base
    prior_full = dag_bkt.get_conditioned_prior("skill_b", learner_masteries={"skill_a": 1.0})
    assert prior_full == 0.20

    # Skill with no parents receives standard base prior
    prior_root = dag_bkt.get_conditioned_prior("skill_a", learner_masteries={})
    assert prior_root == 0.20
