#!/usr/bin/env python3
"""
Comprehensive analysis of LLM strategic deception across all endogenous experiments.

Analyzes:
1. Model strategic profiles (deception rates, coordination patterns)
2. Trust calibration (in-group vs out-group trust)
3. Imposter effects (payoff asymmetries)
4. Temporal dynamics (evolution across 10 rounds)
5. Game-specific patterns
"""

import json
from pathlib import Path
from collections import defaultdict
import numpy as np


def load_all_experiments():
    """Load all experiment files."""
    experiments = {}

    games = ['diners', 'fishing', 'elfarol', 'volunteer']
    conditions = {
        'claude': 'anthropic_claude-opus-4.6_endogenous.json',
        'gpt': 'gpt-5.2_endogenous.json',
        'llama': 'meta-llama_llama-4-maverick_endogenous.json',
        'gpt_imp_llama': 'gpt-5.2_endogenous_imposter_llama.json',
        'llama_imp_gpt': 'meta-llama_llama-4-maverick_endogenous_imposter_gpt.json',
    }

    for game in games:
        experiments[game] = {}
        for cond_name, filename in conditions.items():
            filepath = Path(f'outputs/experiments/{game}/5agents/{filename}')
            if filepath.exists():
                with open(filepath, 'r') as f:
                    experiments[game][cond_name] = json.load(f)

    return experiments


def extract_round0_metrics(exp_data, game_name, condition_name):
    """Extract key metrics from Round 0."""
    round0 = exp_data['rounds'][0]

    metrics = {
        'game': game_name,
        'condition': condition_name,
        'agents': defaultdict(lambda: {
            'payoffs': [],
            'promise_deceptions': [],
            'commitment_breakings': [],
            'premeditated_deceptions': [],
        })
    }

    for trial in round0['trials']:
        for agent_name, agent_data in trial['agents'].items():
            # Payoffs
            payoff = trial['outcomes']['payoffs'][agent_name]
            metrics['agents'][agent_name]['payoffs'].append(payoff)

            # Deception metrics
            promise_dec = agent_data.get('promise_deception')
            commit_break = agent_data.get('commitment_breaking')

            if promise_dec is not None:
                metrics['agents'][agent_name]['promise_deceptions'].append(promise_dec)
            if commit_break is not None:
                metrics['agents'][agent_name]['commitment_breakings'].append(commit_break)

            if promise_dec is not None and commit_break is not None:
                premeditated = promise_dec and commit_break
                metrics['agents'][agent_name]['premeditated_deceptions'].append(premeditated)

    return metrics


def analyze_model_profiles(experiments):
    """Analyze strategic profiles of each model."""
    print("\n" + "="*80)
    print("1. MODEL STRATEGIC PROFILES (Round 0)")
    print("="*80)

    profiles = defaultdict(lambda: {
        'payoffs': [],
        'promise_deception_rates': [],
        'premeditated_deception_rates': [],
        'games': []
    })

    # Homogeneous conditions only
    for game, conditions in experiments.items():
        for model in ['claude', 'gpt', 'llama']:
            if model in conditions:
                metrics = extract_round0_metrics(conditions[model], game, model)

                # Aggregate across all agents
                all_payoffs = []
                all_promise_dec = []
                all_premeditated = []

                for agent_data in metrics['agents'].values():
                    all_payoffs.extend(agent_data['payoffs'])
                    all_promise_dec.extend(agent_data['promise_deceptions'])
                    all_premeditated.extend(agent_data['premeditated_deceptions'])

                profiles[model]['payoffs'].append(np.mean(all_payoffs))
                profiles[model]['promise_deception_rates'].append(np.mean(all_promise_dec))
                profiles[model]['premeditated_deception_rates'].append(np.mean(all_premeditated))
                profiles[model]['games'].append(game)

    # Print summary
    print(f"\n{'Model':<10} {'Mean Payoff':<15} {'Promise Decep':<15} {'Premeditated':<15} {'N Games':<10}")
    print("-"*70)

    for model in ['claude', 'gpt', 'llama']:
        mean_payoff = np.mean(profiles[model]['payoffs'])
        mean_promise = np.mean(profiles[model]['promise_deception_rates'])
        mean_premeditated = np.mean(profiles[model]['premeditated_deception_rates'])
        n_games = len(profiles[model]['games'])

        print(f"{model:<10} {mean_payoff:>14.3f} {mean_promise:>14.1%} {mean_premeditated:>14.1%} {n_games:>9}")

    # Game-by-game breakdown
    print("\n" + "-"*80)
    print("Game-by-Game Breakdown:")
    print("-"*80)

    for game in ['diners', 'fishing', 'elfarol', 'volunteer']:
        print(f"\n{game.upper()}:")
        print(f"{'Model':<10} {'Payoff':<12} {'Promise Dec':<12} {'Premeditated':<12}")

        for model in ['claude', 'gpt', 'llama']:
            if game in experiments and model in experiments[game]:
                metrics = extract_round0_metrics(experiments[game][model], game, model)

                all_payoffs = []
                all_promise = []
                all_premeditated = []

                for agent_data in metrics['agents'].values():
                    all_payoffs.extend(agent_data['payoffs'])
                    all_promise.extend(agent_data['promise_deceptions'])
                    all_premeditated.extend(agent_data['premeditated_deceptions'])

                mean_payoff = np.mean(all_payoffs)
                mean_promise = np.mean(all_promise)
                mean_premeditated = np.mean(all_premeditated)

                print(f"{model:<10} {mean_payoff:>11.3f} {mean_promise:>11.1%} {mean_premeditated:>11.1%}")


def analyze_imposter_effects(experiments):
    """Analyze imposter effect magnitudes."""
    print("\n" + "="*80)
    print("2. IMPOSTER EFFECT ANALYSIS (Round 0)")
    print("="*80)
    print("\nPayoff asymmetries in heterogeneous conditions:")

    for game in ['diners', 'fishing', 'elfarol', 'volunteer']:
        if game not in experiments:
            continue

        print(f"\n{game.upper()}:")
        print("-"*70)

        # Analyze both imposter conditions
        for imp_cond, imp_name, maj_name in [
            ('gpt_imp_llama', 'Llama (J)', 'GPT (M,Q,T,Z)'),
            ('llama_imp_gpt', 'GPT (J)', 'Llama (M,Q,T,Z)')
        ]:
            if imp_cond not in experiments[game]:
                continue

            metrics = extract_round0_metrics(experiments[game][imp_cond], game, imp_cond)

            # J is always the imposter
            j_payoffs = metrics['agents']['J']['payoffs']

            # Others are majority
            maj_payoffs = []
            for agent in ['M', 'Q', 'T', 'Z']:
                maj_payoffs.extend(metrics['agents'][agent]['payoffs'])

            j_mean = np.mean(j_payoffs)
            maj_mean = np.mean(maj_payoffs)
            diff = maj_mean - j_mean

            print(f"\n  Imposter: {imp_name}")
            print(f"    J (minority):  {j_mean:>7.3f} payoff")
            print(f"    Majority:      {maj_mean:>7.3f} payoff")
            print(f"    Difference:    {diff:>+7.3f} (majority advantage)")

            # Direction indicator
            if abs(diff) > 1.0:
                if diff > 0:
                    print(f"    → Minority EXPLOITED (majority profits +{diff:.2f})")
                else:
                    print(f"    → Minority PROFITS (advantage {abs(diff):.2f})")


def analyze_trust_patterns(experiments):
    """Analyze trust calibration patterns."""
    print("\n" + "="*80)
    print("3. TRUST CALIBRATION ANALYSIS")
    print("="*80)

    print("\nAnalyzing trust scores from Round 1 onwards...")
    print("(Trust scores reflect agent's assessment after seeing outcomes)")

    trust_patterns = defaultdict(lambda: defaultdict(list))

    for game in ['diners', 'fishing', 'elfarol', 'volunteer']:
        if game not in experiments:
            continue

        # Homogeneous conditions: in-group trust
        for model in ['claude', 'gpt', 'llama']:
            if model not in experiments[game]:
                continue

            exp_data = experiments[game][model]

            # Look at Rounds 1-9 (after reflection from previous round)
            for round_data in exp_data['rounds'][1:]:
                for trial in round_data['trials']:
                    for agent_name, agent_data in trial['agents'].items():
                        if 'reflection' in agent_data and 'takeaways' in agent_data['reflection']:
                            takeaways = agent_data['reflection']['takeaways']
                            for other_agent, assessment in takeaways.items():
                                if isinstance(assessment, dict) and 'score' in assessment:
                                    trust_patterns[f'{model}_ingroup']['scores'].append(assessment['score'])

        # Imposter conditions: out-group trust
        for imp_cond, minority_agent in [
            ('gpt_imp_llama', 'J'),  # J=Llama
            ('llama_imp_gpt', 'J')   # J=GPT
        ]:
            if imp_cond not in experiments[game]:
                continue

            exp_data = experiments[game][imp_cond]
            minority_model = 'llama' if 'gpt_imp' in imp_cond else 'gpt'
            majority_model = 'gpt' if minority_model == 'llama' else 'llama'

            for round_data in exp_data['rounds'][1:]:
                for trial in round_data['trials']:
                    for agent_name, agent_data in trial['agents'].items():
                        if 'reflection' not in agent_data or 'takeaways' not in agent_data['reflection']:
                            continue

                        takeaways = agent_data['reflection']['takeaways']

                        for other_agent, assessment in takeaways.items():
                            if not isinstance(assessment, dict) or 'score' not in assessment:
                                continue

                            # Classify the trust type
                            if agent_name == 'J':
                                # Minority trusting majority
                                trust_patterns[f'{minority_model}_minority_to_majority']['scores'].append(assessment['score'])
                            elif other_agent == 'J':
                                # Majority trusting minority
                                trust_patterns[f'{majority_model}_majority_to_minority']['scores'].append(assessment['score'])
                            else:
                                # Majority trusting majority (within-group)
                                trust_patterns[f'{majority_model}_majority_ingroup']['scores'].append(assessment['score'])

    # Print summary
    print(f"\n{'Pattern':<40} {'Mean Trust':<12} {'N Samples':<12}")
    print("-"*70)

    for pattern, data in sorted(trust_patterns.items()):
        if len(data['scores']) > 0:
            mean_trust = np.mean(data['scores'])
            n = len(data['scores'])
            print(f"{pattern:<40} {mean_trust:>11.2f} {n:>11}")


def analyze_temporal_dynamics(experiments):
    """Analyze how patterns evolve across 10 rounds."""
    print("\n" + "="*80)
    print("4. TEMPORAL DYNAMICS (Round-by-Round Evolution)")
    print("="*80)

    # Focus on Diners (clearest signal from previous analysis)
    game = 'diners'

    if game not in experiments:
        print(f"\n{game} not found in experiments")
        return

    print(f"\nAnalyzing {game.upper()} across 10 rounds...")
    print("(Does the imposter effect persist, amplify, or diminish?)")

    for imp_cond, imp_label in [
        ('gpt_imp_llama', 'J=Llama (minority) in GPT majority'),
        ('llama_imp_gpt', 'J=GPT (minority) in Llama majority')
    ]:
        if imp_cond not in experiments[game]:
            continue

        print(f"\n{imp_label}:")
        print("-"*70)
        print(f"{'Round':<8} {'J Payoff':<12} {'Majority Payoff':<18} {'Difference':<12}")
        print("-"*70)

        exp_data = experiments[game][imp_cond]

        for round_data in exp_data['rounds']:
            round_id = round_data['round_id']

            j_payoffs = []
            maj_payoffs = []

            for trial in round_data['trials']:
                j_payoffs.append(trial['outcomes']['payoffs']['J'])
                for agent in ['M', 'Q', 'T', 'Z']:
                    maj_payoffs.append(trial['outcomes']['payoffs'][agent])

            j_mean = np.mean(j_payoffs)
            maj_mean = np.mean(maj_payoffs)
            diff = maj_mean - j_mean

            print(f"{round_id:<8} {j_mean:>11.3f} {maj_mean:>17.3f} {diff:>+11.3f}")


def analyze_game_mechanics(experiments):
    """Analyze how game mechanics affect patterns."""
    print("\n" + "="*80)
    print("5. GAME MECHANICS ANALYSIS")
    print("="*80)

    print("\nClassifying games by decision structure:")
    print("-"*70)

    game_types = {
        'Binary choice games': ['diners'],
        'Multi-level games': ['fishing', 'volunteer'],
        'Threshold games': ['elfarol']
    }

    for game_type, game_list in game_types.items():
        print(f"\n{game_type}:")
        for game in game_list:
            print(f"  - {game}")

    print("\n" + "-"*70)
    print("Imposter effect magnitude by game type:")
    print("-"*70)

    for game in ['diners', 'fishing', 'elfarol', 'volunteer']:
        if game not in experiments:
            continue

        print(f"\n{game.upper()}:")

        for imp_cond in ['gpt_imp_llama', 'llama_imp_gpt']:
            if imp_cond not in experiments[game]:
                continue

            metrics = extract_round0_metrics(experiments[game][imp_cond], game, imp_cond)

            j_payoffs = metrics['agents']['J']['payoffs']
            maj_payoffs = []
            for agent in ['M', 'Q', 'T', 'Z']:
                maj_payoffs.extend(metrics['agents'][agent]['payoffs'])

            j_mean = np.mean(j_payoffs)
            maj_mean = np.mean(maj_payoffs)
            diff = maj_mean - j_mean

            imp_label = 'J=Llama' if 'gpt_imp' in imp_cond else 'J=GPT'
            print(f"  {imp_label}: difference = {diff:+.3f}")


def main():
    print("="*80)
    print("COMPREHENSIVE ANALYSIS OF LLM STRATEGIC DECEPTION")
    print("="*80)
    print("\nDataset: 4 games × 5 conditions × 20 trials × 10 rounds")
    print("Total: 4,000 game instances analyzed")

    # Load all experiments
    print("\nLoading experiments...")
    experiments = load_all_experiments()

    loaded_count = sum(len(conditions) for conditions in experiments.values())
    print(f"Loaded: {loaded_count} experiment files")

    # Run analyses
    analyze_model_profiles(experiments)
    analyze_imposter_effects(experiments)
    analyze_trust_patterns(experiments)
    analyze_temporal_dynamics(experiments)
    analyze_game_mechanics(experiments)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
