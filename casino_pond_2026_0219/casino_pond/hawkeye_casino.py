#!/usr/local/bin/python3.12
"""Main entry point for CASINO Hawkeye Analysis Tool"""

import sys
import argparse

from hawkeye_casino.core.analyzer import HawkeyeAnalyzer
from hawkeye_casino.gui import GUI_AVAILABLE


def main():
    parser = argparse.ArgumentParser(
        description="CASINO Hawkeye Analysis Tool - Lists Run Versions by Default",
        epilog="""
Examples:
  %(prog)s                    # Start GUI to list run versions (default)
  %(prog)s -discovery         # Start GUI to list run versions
  %(prog)s -console           # Use console mode to list run versions
  %(prog)s -list              # List run versions in console
  %(prog)s -analyze-all       # Legacy mode: analyze all runs (not recommended)
        """
    )
    parser.add_argument('-config', type=str, help='Path to vista_casino.yaml configuration file')
    parser.add_argument('-run', type=str, help='Analyze specific run path')
    parser.add_argument('-console', action='store_true', help='Use console mode instead of GUI')
    parser.add_argument('-list', action='store_true',
                       help='List available run versions without analysis (console mode)')
    parser.add_argument('-discovery', action='store_true',
                       help='Discovery mode: List run versions in GUI without analysis (default)')
    parser.add_argument('-analyze-all', action='store_true',
                       help='Analyze all runs (legacy mode - not recommended)')

    args = parser.parse_args()

    analyzer = HawkeyeAnalyzer(args.config)

    if args.list:
        runs = analyzer.discover_runs(detailed_check=False)
        if runs:
            print(f"\nFound {len(runs)} run versions:")
            for i, run in enumerate(runs):
                print(f"{i+1}. {run['run_version']} (in {run['relative_path']})")
        else:
            print("No run versions found.")
        return

    if args.analyze_all:
        print("WARNING: Analyzing all runs may be slow for large projects.")
        print("Consider using discovery mode and 'Gather Selected' instead.")
        run_analysis(analyzer, args.run, not args.console, False)
    elif args.console:
        run_analysis(analyzer, args.run, False, True)
    else:
        try:
            run_analysis(analyzer, args.run, True, True)
        except Exception as e:
            print(f"GUI mode failed: {e}")
            print("Falling back to console mode...")
            run_analysis(analyzer, args.run, False, True)


def run_analysis(analyzer, run_path, start_gui, discovery_only):
    """Run analysis with specified parameters"""
    print("Starting CASINO Hawkeye Analysis in Discovery Mode..." if discovery_only
          else "Starting CASINO Hawkeye Analysis...")

    if run_path:
        if os.path.exists(run_path):
            run_data = analyzer.analyze_run(run_path)
            analyzer.analysis_results[run_path] = run_data
        else:
            print(f"Error: Run path {run_path} does not exist")
            return
    else:
        runs = analyzer.discover_runs(detailed_check=False)

        if not runs:
            print("No runs found. Please check the workspace hierarchy.")
            return

        print("\nAvailable Run Versions:")
        for i, run in enumerate(runs):
            print(f"{i+1}. {run['run_version']} (in {run['relative_path']})")

        print(f"\nDiscovery mode: Found {len(runs)} run versions.")
        print("Use 'Refresh Analysis' in the GUI to update the list based on filters.")
        print("Use 'Gather Selected' to analyze specific runs.")
        analyzer.analysis_results = {}

    if start_gui and GUI_AVAILABLE:
        from hawkeye_casino.gui.dashboard import HawkeyeDashboard
        from PyQt5.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        main_window = HawkeyeDashboard(analyzer, analyzer.analysis_results)
        main_window.show()

        if app and main_window:
            app.exec_()
        else:
            print("GUI creation failed, falling back to console mode...")
            print_console_results(analyzer)
    else:
        print_console_results(analyzer)


def print_console_results(analyzer):
    """Print analysis results to console"""
    print("\n" + "="*80)
    print("CASINO Hawkeye ANALYSIS RESULTS")
    print("="*80)

    if not analyzer.analysis_results:
        print("\nNo analysis results available.")
        print("Discovery mode: Run versions found but not yet analyzed.")
        print("Use GUI and 'Gather Selected' to analyze specific runs.")
        return

    for run_path, run_data in analyzer.analysis_results.items():
        print(f"\nRun: {run_path}")

        if 'summary' in run_data:
            print(f"Status: {run_data['summary']['successful_tasks']}/"
                  f"{run_data['summary']['total_tasks']} tasks successful")
            print(f"Completion Rate: {run_data['summary']['completion_rate']:.1f}%")

        if 'jobs' in run_data:
            for job_name, job_data in run_data['jobs'].items():
                print(f"\n  Job: {job_name}")
                for task_name, task_data in job_data.get('tasks', {}).items():
                    print(f"    {task_name}: {task_data.get('status', 'unknown').upper()}")
                    for keyword_name, keyword_data in task_data.get('keywords', {}).items():
                        if keyword_data.get('value') is not None:
                            print(f"      {keyword_name}: {keyword_data['value']}"
                                  f"{keyword_data.get('unit', '')}")
                        else:
                            print(f"      {keyword_name}: -")


if __name__ == "__main__":
    main()
