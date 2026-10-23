"""
Calculate theoretical base rates for lying opportunities by game.

For each game, compute the fraction of announcement profiles that admit
at least one deviation of each category (strategic, selfish, altruistic, sabotaging).

These are theoretical base rates determined purely by game structure, independent of model behavior.
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root

from src.scenario_enumeration.core.scenario_generator import generate_scenarios
from src.theory.lying_categories import analyze_decision


def calculate_base_rates_for_game(game_type: str, n_agents: int = 5):
    """
    Calculate base rates for a single game.

    Returns:
        Dict with fraction of profiles admitting each category
    """
    # Agent names
    agent_names = [chr(65 + i) for i in range(n_agents)]  # A, B, C, D, E

    # Generate all canonical scenarios (use base game name, not _single_agent suffix)
    scenario_generator = generate_scenarios(
        game_type=game_type,
        agent_names=agent_names
    )

    # Track which profiles admit each category
    profiles_with_category = {
        'strategic': set(),
        'selfish': set(),
        'altruistic': set(),
        'sabotaging': set()
    }

    total_profiles = 0

    for scenario in scenario_generator:
        total_profiles += 1

        # Extract scenario info
        agent_name = scenario['agent_name']
        announced = scenario['announced']

        # For single-agent games, we need to reconstruct the full announcement profile
        # The scenario dict has the aggregate info, but we need to check all alternatives

        # Get all possible actions for this game
        if game_type in ['fishing', 'publicgoods', 'weakestlink']:
            all_actions = list(range(0, 6))  # 0-5
        elif game_type in ['volunteer', 'elfarol', 'diners']:
            all_actions = ['YES', 'NO'] if game_type == 'volunteer' else ['GO', 'STAY'] if game_type == 'elfarol' else ['EXPENSIVE', 'CHEAP']
        else:
            continue

        # Check each alternative action
        categories_found = set()

        for alternative in all_actions:
            # Skip if same as announced
            if alternative == announced:
                continue

            try:
                # Analyze this deviation
                analysis = analyze_decision(
                    game_type=f"{game_type}_single_agent",
                    agent_name=agent_name,
                    announced=announced,
                    actual=alternative,
                    scenario=scenario,
                    game_params={},
                    n_agents=n_agents
                )

                if analysis.get('lied'):
                    category = analysis.get('lie_category')
                    if category in ['strategic', 'selfish', 'altruistic', 'sabotaging']:
                        categories_found.add(category)

            except Exception as e:
                # Skip if analysis fails
                continue

        # Mark this profile as having opportunities for each category found
        for category in categories_found:
            profiles_with_category[category].add(total_profiles)

    # Calculate fractions
    base_rates = {}
    for category in ['strategic', 'selfish', 'altruistic', 'sabotaging']:
        count = len(profiles_with_category[category])
        base_rates[category] = 100 * count / total_profiles if total_profiles > 0 else 0.0

    base_rates['total_profiles'] = total_profiles
    base_rates['profiles_per_category'] = {k: len(v) for k, v in profiles_with_category.items()}

    return base_rates


def main():
    """Calculate base rates for all games."""
    games = ['fishing', 'publicgoods', 'weakestlink', 'volunteer', 'diners', 'elfarol']
    n_agents = 5

    print("=" * 100)
    print("THEORETICAL BASE RATES FOR LYING OPPORTUNITIES (5 AGENTS)")
    print("=" * 100)
    print()
    print("Base rates computed algorithmically from game structure.")
    print("Shows fraction of announcement profiles admitting at least one deviation of each category.")
    print("Games with zero base rate for a category cannot produce that type of lie.")
    print()

    all_results = {}

    for game in games:
        print(f"\nAnalyzing {game}...")
        base_rates = calculate_base_rates_for_game(game, n_agents)
        all_results[game] = base_rates

    # Print results table
    print("\n" + "=" * 100)
    print("BASE RATES TABLE")
    print("=" * 100)
    print()
    print(f"{'Game':<15} {'Total Profiles':<15} {'Strategic %':<15} {'Selfish %':<15} {'Altruistic %':<15} {'Sabotaging %':<15}")
    print("-" * 100)

    for game in games:
        results = all_results[game]
        print(f"{game.upper():<15} "
              f"{results['total_profiles']:<15} "
              f"{results['strategic']:<15.1f} "
              f"{results['selfish']:<15.1f} "
              f"{results['altruistic']:<15.1f} "
              f"{results['sabotaging']:<15.1f}")

    # Print detailed breakdown
    print("\n\n" + "=" * 100)
    print("DETAILED BREAKDOWN")
    print("=" * 100)

    for game in games:
        results = all_results[game]
        print(f"\n{game.upper()}:")
        print(f"  Total canonical profiles: {results['total_profiles']}")
        print(f"  Profiles with strategic opportunity:  {results['profiles_per_category']['strategic']:>4} ({results['strategic']:>5.1f}%)")
        print(f"  Profiles with selfish opportunity:    {results['profiles_per_category']['selfish']:>4} ({results['selfish']:>5.1f}%)")
        print(f"  Profiles with altruistic opportunity: {results['profiles_per_category']['altruistic']:>4} ({results['altruistic']:>5.1f}%)")
        print(f"  Profiles with sabotaging opportunity: {results['profiles_per_category']['sabotaging']:>4} ({results['sabotaging']:>5.1f}%)")

    # Identify zero base rate cases
    print("\n\n" + "=" * 100)
    print("ZERO BASE RATE CATEGORIES (Structurally Impossible)")
    print("=" * 100)

    for game in games:
        results = all_results[game]
        zero_categories = [cat for cat in ['strategic', 'selfish', 'altruistic', 'sabotaging']
                          if results[cat] == 0.0]

        if zero_categories:
            print(f"\n{game.upper()}: {', '.join(zero_categories)}")
        else:
            print(f"\n{game.upper()}: (all categories possible)")

    print("\n" + "=" * 100)
    print("END OF ANALYSIS")
    print("=" * 100)

    # Save results
    output_dir = Path(__file__).parent.parent / "outputs"
    output_file = output_dir / "THEORETICAL_BASE_RATES.txt"

    with open(output_file, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("THEORETICAL BASE RATES FOR LYING OPPORTUNITIES (5 AGENTS)\n")
        f.write("=" * 100 + "\n\n")
        f.write("Base rates computed algorithmically from game structure.\n")
        f.write("Shows fraction of announcement profiles admitting at least one deviation of each category.\n")
        f.write("Games with zero base rate cannot produce that type of lie regardless of model behavior.\n\n")

        f.write("=" * 100 + "\n")
        f.write("BASE RATES TABLE\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"{'Game':<15} {'Total Profiles':<15} {'Strategic %':<15} {'Selfish %':<15} {'Altruistic %':<15} {'Sabotaging %':<15}\n")
        f.write("-" * 100 + "\n")

        for game in games:
            results = all_results[game]
            f.write(f"{game.upper():<15} "
                  f"{results['total_profiles']:<15} "
                  f"{results['strategic']:<15.1f} "
                  f"{results['selfish']:<15.1f} "
                  f"{results['altruistic']:<15.1f} "
                  f"{results['sabotaging']:<15.1f}\n")

        f.write("\n\n" + "=" * 100 + "\n")
        f.write("DETAILED BREAKDOWN\n")
        f.write("=" * 100 + "\n")

        for game in games:
            results = all_results[game]
            f.write(f"\n{game.upper()}:\n")
            f.write(f"  Total canonical profiles: {results['total_profiles']}\n")
            f.write(f"  Profiles with strategic opportunity:  {results['profiles_per_category']['strategic']:>4} ({results['strategic']:>5.1f}%)\n")
            f.write(f"  Profiles with selfish opportunity:    {results['profiles_per_category']['selfish']:>4} ({results['selfish']:>5.1f}%)\n")
            f.write(f"  Profiles with altruistic opportunity: {results['profiles_per_category']['altruistic']:>4} ({results['altruistic']:>5.1f}%)\n")
            f.write(f"  Profiles with sabotaging opportunity: {results['profiles_per_category']['sabotaging']:>4} ({results['sabotaging']:>5.1f}%)\n")

        f.write("\n\n" + "=" * 100 + "\n")
        f.write("ZERO BASE RATE CATEGORIES (Structurally Impossible)\n")
        f.write("=" * 100 + "\n")

        for game in games:
            results = all_results[game]
            zero_categories = [cat for cat in ['strategic', 'selfish', 'altruistic', 'sabotaging']
                              if results[cat] == 0.0]

            if zero_categories:
                f.write(f"\n{game.upper()}: {', '.join(zero_categories)}\n")
            else:
                f.write(f"\n{game.upper()}: (all categories possible)\n")

        f.write("\n" + "=" * 100 + "\n")
        f.write("END OF ANALYSIS\n")
        f.write("=" * 100 + "\n")

    print(f"\n\nResults saved to: {output_file}")


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
