from __future__ import annotations

VALID_REGIMES = {
    'baseline',
    'low_correlation',
    'high_correlation',
    'sparse_covariance',
    'clustered_assets',
    'hard_budget',
}
VALID_EXECUTION_MODES = {'fast_simulator', 'aer_sampler', 'runtime_sampler'}
VALID_NOISE_MODELS = {'ideal', 'depolarizing', 'thermal_relaxation'}
VALID_BO_ACQUISITIONS = {'ucb', 'logei'}
VALID_BO_TARGETS = {'raw', 'feasibility_aware'}
VALID_BO_HIGH_DIM_STRATEGIES = {'none', 'random_embedding'}
VALID_QPU_BILLING_BASIS = {'execution', 'total'}
VALID_EXECUTION_BILLING_MODES = {'job', 'session'}
VALID_TRANSPILE_TOPOLOGIES = {
    'auto',
    'backend_native',
    'all_to_all',
    'heavy_hex_3',
    'heavy_hex_5',
    'heavy_hex_7',
}
VALID_ROUTING_METHODS = {'basic', 'lookahead', 'none', 'sabre', 'stochastic'}
VALID_MIXER_TYPES = {'xy', 'product_x'}
VALID_TRANSPILE_OPTIMIZATION_LEVELS = {0, 1, 2, 3}

FAST_SIM_MAX_ASSETS = 12
DEFAULT_SUITE_OUTPUT_DIR = 'results/multi_regime_suite'
DEFAULT_SUITE_TITLE = 'Portfolio QAOA characterisation suite'
DEFAULT_CLI_DESCRIPTION = 'Portfolio QAOA characterisation study'
PAYLOAD_SCHEMA_VERSION = '1.6'
RESEARCH_QUESTION = (
    'When does a more sophisticated classical optimizer justify its runtime, shot, queue, '
    'and mitigation cost for constrained QAOA portfolio optimization?'
)
BOOTSTRAP_SEEDS = {
    'raw': 17,
    'feasible': 23,
    'win': 31,
}

__all__ = [
    'VALID_REGIMES',
    'VALID_EXECUTION_MODES',
    'VALID_NOISE_MODELS',
    'VALID_BO_ACQUISITIONS',
    'VALID_BO_TARGETS',
    'VALID_BO_HIGH_DIM_STRATEGIES',
    'VALID_QPU_BILLING_BASIS',
    'VALID_EXECUTION_BILLING_MODES',
    'VALID_TRANSPILE_TOPOLOGIES',
    'VALID_ROUTING_METHODS',
    'VALID_MIXER_TYPES',
    'VALID_TRANSPILE_OPTIMIZATION_LEVELS',
    'FAST_SIM_MAX_ASSETS',
    'DEFAULT_SUITE_OUTPUT_DIR',
    'DEFAULT_SUITE_TITLE',
    'DEFAULT_CLI_DESCRIPTION',
    'PAYLOAD_SCHEMA_VERSION',
    'RESEARCH_QUESTION',
    'BOOTSTRAP_SEEDS',
]
