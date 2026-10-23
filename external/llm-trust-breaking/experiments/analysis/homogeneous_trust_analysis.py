#!/usr/bin/env python3
"""
Analyze announcement trust in homogeneous conditions.
Question: Does Llama trust other Llamas the same way they trust GPT?
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import statistics

def load_homogeneous_round0():
    """Load Round 0 from homogeneous conditions."""
    games = ['diners', 'fishing']
    data = {}

    for game in games:
        data[game] = {}

        # All GPT
        gpt_path = f'outputs/experiments/{game}/5agents/gpt-5.2_endogenous.json'
        if Path(gpt_path).exists():
            with open(gpt_path) as f:
                full_data = json.load(f)
                data[game]['all_gpt'] = {
                    'metadata': full_data['metadata'],
                    'round0': [r for r in full_data['rounds'] if r['round_id'] == 0][0]
                }

        # All Llama
        llama_path = f'outputs/experiments/{game}/5agents/llama-4-maverick_endogenous.json'
        if Path(llama_path).exists():
            with open(llama_path) as f:
                full_data = json.load(f)
                data[game]['all_llama'] = {
                    'metadata': full_data['metadata'],
                    'round0': [r for r in full_data['rounds'] if r['round_id'] == 0][0]
                }

    return data

def analyze_announcement_response(round0_data, condition_name):
    """Check if agents respond to others' announcements."""
    print(f"\n{'='*120}")
    print(f"ANNOUNCEMENT-ACTION ANALYSIS: {condition_name}")
    print(f"{'='*120}")

    # For each trial, check if agents choose what others announced
    trials_analysis = []

    for trial in round0_data['trials']:
        trial_id = trial['trial_id']

        # Collect all announcements and choices
        announcements = {}
        choices = {}

        for agent_name in ['J', 'M', 'Q', 'T', 'Z']:
            if agent_name in trial['agents']:
                agent_data = trial['agents'][agent_name]
                announcements[agent_name] = agent_data.get('stage2', {}).get('stated_action', 'UNKNOWN')
                choices[agent_name] = agent_data.get('stage3', {}).get('choice', 'UNKNOWN')

        # For each agent, check if they matched others' announcements
        for focal_agent in announcements.keys():
            others_announced = [announcements[a] for a in announcements if a != focal_agent]
            focal_choice = choices[focal_agent]

            # Count how many others announced CHEAP/EXPENSIVE
            others_cheap = sum(1 for a in others_announced if a == 'CHEAP')
            others_expensive = sum(1 for a in others_announced if a == 'EXPENSIVE')

            # Majority announcement
            if others_cheap > others_expensive:
                majority_announced = 'CHEAP'
            elif others_expensive > others_cheap:
                majority_announced = 'EXPENSIVE'
            else:
                majority_announced = 'TIE'

            # Did focal agent match the majority announcement?
            matched = focal_choice == majority_announced if majority_announced != 'TIE' else None

            trials_analysis.append({
                'trial_id': trial_id,
                'focal_agent': focal_agent,
                'focal_choice': focal_choice,
                'others_cheap': others_cheap,
                'others_expensive': others_expensive,
                'majority_announced': majority_announced,
                'matched_majority': matched
            })

    # Summarize
    print(f"\nSample trials (first 5):")
    print(f"{'Trial':<8} {'Agent':<8} {'Others Ann.':<20} {'Agent Choice':<15} {'Matched?':<10}")
    print("-" * 70)

    for entry in trials_analysis[:5]:
        others_summary = f"{entry['others_cheap']}C / {entry['others_expensive']}E"
        matched_str = str(entry['matched_majority']) if entry['matched_majority'] is not None else 'TIE'
        print(f"{entry['trial_id']:<8} {entry['focal_agent']:<8} {others_summary:<20} {entry['focal_choice']:<15} {matched_str:<10}")

    # Overall statistics
    valid_matches = [e for e in trials_analysis if e['matched_majority'] is not None]
    if valid_matches:
        match_rate = sum(1 for e in valid_matches if e['matched_majority']) / len(valid_matches) * 100
        print(f"\n{'='*70}")
        print(f"OVERALL: {match_rate:.1f}% of agents matched the majority announcement")
        print(f"  ({sum(1 for e in valid_matches if e['matched_majority'])}/{len(valid_matches)} instances)")
        print(f"{'='*70}")

        if match_rate > 60:
            print("  → HIGH trust in announcements (agents follow what others say)")
        elif match_rate < 40:
            print("  → LOW trust in announcements (agents ignore what others say)")
        else:
            print("  → MODERATE trust in announcements")

    # Breakdown by what was announced
    print(f"\nBREAKDOWN BY ANNOUNCEMENT:")
    print("-" * 70)

    # When majority announced CHEAP, how often did agents choose CHEAP?
    cheap_announced = [e for e in trials_analysis if e['majority_announced'] == 'CHEAP']
    if cheap_announced:
        cheap_matched = sum(1 for e in cheap_announced if e['matched_majority']) / len(cheap_announced) * 100
        print(f"When majority announced CHEAP: {cheap_matched:.1f}% chose CHEAP ({sum(1 for e in cheap_announced if e['matched_majority'])}/{len(cheap_announced)})")

    # When majority announced EXPENSIVE, how often did agents choose EXPENSIVE?
    expensive_announced = [e for e in trials_analysis if e['majority_announced'] == 'EXPENSIVE']
    if expensive_announced:
        expensive_matched = sum(1 for e in expensive_announced if e['matched_majority']) / len(expensive_announced) * 100
        print(f"When majority announced EXPENSIVE: {expensive_matched:.1f}% chose EXPENSIVE ({sum(1 for e in expensive_announced if e['matched_majority'])}/{len(expensive_announced)})")

    return trials_analysis

def compare_ingroup_vs_outgroup():
    """Compare trust in same-model vs different-model announcements."""
    print(f"\n{'='*120}")
    print("IN-GROUP VS OUT-GROUP TRUST COMPARISON")
    print(f"{'='*120}")

    # Load all data (homogeneous + imposter)
    homo_data = load_homogeneous_round0()

    # Load imposter data
    imposter_data = {}
    for game in ['diners', 'fishing']:
        imposter_data[game] = {}

        # Llama minority (Llama seeing GPT)
        llama_min_path = f'outputs/experiments/{game}/5agents/gpt-5.2_endogenous_imposter.json'
        if Path(llama_min_path).exists():
            with open(llama_min_path) as f:
                full_data = json.load(f)
                imposter_data[game]['llama_minority'] = {
                    'round0': [r for r in full_data['rounds'] if r['round_id'] == 0][0]
                }

        # GPT minority (GPT seeing Llama)
        gpt_min_path = f'outputs/experiments/{game}/5agents/meta-llama_llama-4-maverick_endogenous_imposter.json'
        if Path(gpt_min_path).exists():
            with open(gpt_min_path) as f:
                full_data = json.load(f)
                imposter_data[game]['gpt_minority'] = {
                    'round0': [r for r in full_data['rounds'] if r['round_id'] == 0][0]
                }

    # Focus on Diners
    game = 'diners'

    print(f"\nDINERS GAME - Round 0 Announcement Trust:")
    print("-" * 120)

    # Llama in-group (all Llama)
    print("\n1. LLAMA IN-GROUP (All Llama condition):")
    print("   Question: Do Llama agents trust other Llamas' announcements?")
    llama_homo_analysis = analyze_announcement_response(homo_data[game]['all_llama']['round0'], "All Llama")

    # Llama out-group (Llama minority seeing GPT majority)
    print("\n2. LLAMA OUT-GROUP (Llama minority, GPT majority):")
    print("   Question: Do Llama agents (as minority J) cooperate when GPT announces cooperation?")
    print("   Note: In this condition, Llama is agent J (minority), so we check GPT majority's response")
    print("   Actually, we want to know: Do GPT agents respond to Llama's announcements?")

    # Actually we want the opposite - check GPT majority's response to Llama minority
    # But we already know this from earlier analysis - GPT ignores announcements

    # Better: Check Llama MAJORITY's response in GPT-minority condition
    print("\n3. LLAMA MAJORITY (GPT minority condition):")
    print("   Question: Do Llama agents (as majority) trust GPT's announcements?")

    # Extract Llama majority behavior in GPT-minority condition
    gpt_min_trials = imposter_data[game]['gpt_minority']['round0']['trials']

    llama_responses = []
    for trial in gpt_min_trials:
        # GPT is agent J
        if 'J' in trial['agents']:
            gpt_announcement = trial['agents']['J'].get('stage2', {}).get('stated_action', 'UNKNOWN')

            # Check Llama agents (M, Q, T, Z)
            for agent in ['M', 'Q', 'T', 'Z']:
                if agent in trial['agents']:
                    llama_choice = trial['agents'][agent].get('stage3', {}).get('choice', 'UNKNOWN')
                    llama_responses.append({
                        'gpt_announced': gpt_announcement,
                        'llama_chose': llama_choice,
                        'matched': gpt_announcement == llama_choice
                    })

    if llama_responses:
        match_rate = sum(1 for r in llama_responses if r['matched']) / len(llama_responses) * 100
        print(f"\n   When GPT announced, Llama majority matched {match_rate:.1f}% of the time")

        # Breakdown
        cheap_announced = [r for r in llama_responses if r['gpt_announced'] == 'CHEAP']
        if cheap_announced:
            cheap_match = sum(1 for r in cheap_announced if r['matched']) / len(cheap_announced) * 100
            print(f"   When GPT announced CHEAP: {cheap_match:.1f}% of Llamas chose CHEAP ({sum(1 for r in cheap_announced if r['matched'])}/{len(cheap_announced)})")

    # GPT in-group (all GPT)
    print("\n4. GPT IN-GROUP (All GPT condition):")
    print("   Question: Do GPT agents trust other GPTs' announcements?")
    gpt_homo_analysis = analyze_announcement_response(homo_data[game]['all_gpt']['round0'], "All GPT")

    # Summary comparison
    print(f"\n{'='*120}")
    print("SUMMARY COMPARISON")
    print(f"{'='*120}")

    # Extract match rates
    llama_homo_valid = [e for e in llama_homo_analysis if e['matched_majority'] is not None]
    gpt_homo_valid = [e for e in gpt_homo_analysis if e['matched_majority'] is not None]

    llama_homo_rate = sum(1 for e in llama_homo_valid if e['matched_majority']) / len(llama_homo_valid) * 100 if llama_homo_valid else 0
    gpt_homo_rate = sum(1 for e in gpt_homo_valid if e['matched_majority']) / len(gpt_homo_valid) * 100 if gpt_homo_valid else 0

    print(f"\nLlama trust in other Llamas (in-group): {llama_homo_rate:.1f}%")
    print(f"Llama trust in GPT (out-group): {match_rate:.1f}%")
    print(f"GPT trust in other GPTs (in-group): {gpt_homo_rate:.1f}%")

    print("\nINTERPRETATION:")
    if match_rate > llama_homo_rate + 10:
        print("  → LLAMA SHOWS OUT-GROUP BIAS: Trusts GPT MORE than other Llamas!")
    elif llama_homo_rate > match_rate + 10:
        print("  → LLAMA SHOWS IN-GROUP BIAS: Trusts Llamas MORE than GPT")
    else:
        print("  → LLAMA TRUSTS ANNOUNCEMENTS GENERALLY (similar rates)")

    if gpt_homo_rate < 40:
        print("  → GPT SHOWS SKEPTICISM: Doesn't trust announcements (in-group or out-group)")

def main():
    """Run homogeneous trust analysis."""
    print("="*120)
    print("HOMOGENEOUS ANNOUNCEMENT TRUST ANALYSIS")
    print("="*120)
    print("\nQuestion: Do Llama agents trust other Llamas' announcements?")
    print("Context: We know Llama majority trusts GPT minority's announcements (90% cooperation)")
    print()

    compare_ingroup_vs_outgroup()

    print("\n" + "="*120)
    print("ANALYSIS COMPLETE")
    print("="*120)

if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, KeyError) as e:
        sys.exit(
            "\nThis script analyses result files from the original study, and the ones it\n"
            f"expects were not found under outputs/ ({e!r}).\n"
            "Run the matching experiment first, or point the paths at the top of this\n"
            "file at your own results."
        )
