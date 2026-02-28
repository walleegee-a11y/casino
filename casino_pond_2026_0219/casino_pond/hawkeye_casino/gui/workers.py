"""Background worker threads for GUI operations"""

import os
import datetime
from typing import Dict, Any, Set

try:
    from PyQt5.QtCore import QThread, pyqtSignal
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    QThread = object
    def pyqtSignal(*args, **kwargs):
        return None


if GUI_AVAILABLE:
    class BackgroundWorker(QThread):
        """Worker thread for background analysis with progress updates"""
        progress_update = pyqtSignal(int, int, str)
        finished_signal = pyqtSignal(object)

        def __init__(self, analyzer, selected_analysis):
            super().__init__()
            self.analyzer = analyzer
            self.selected_analysis = selected_analysis
            self._is_running = True

        def run(self):
            """Run analysis operation"""
            try:
                total_tasks = sum(sum(len(tasks) for tasks in jobs.values())
                                 for jobs in self.selected_analysis.values())
                current_task = 0

                filtered_analysis = self.analyzer.pre_filter_analysis_tasks(self.selected_analysis)

                for run_path, selected_jobs in filtered_analysis.items():
                    if not self._is_running or not os.path.exists(run_path):
                        continue

                    if run_path not in self.analyzer.analysis_results:
                        self.analyzer.analysis_results[run_path] = {
                            'path': run_path,
                            'jobs': {},
                            'summary': {},
                            'last_updated': datetime.datetime.now().isoformat()
                        }

                    for job_name, selected_tasks in selected_jobs.items():
                        if not self._is_running:
                            break

                        if 'jobs' not in self.analyzer.analysis_results[run_path]:
                            self.analyzer.analysis_results[run_path]['jobs'] = {}
                        if job_name not in self.analyzer.analysis_results[run_path]['jobs']:
                            self.analyzer.analysis_results[run_path]['jobs'][job_name] = {
                                'path': os.path.join(run_path, job_name),
                                'tasks': {},
                                'summary': {}
                            }

                        for task_name in selected_tasks:
                            if not self._is_running:
                                break

                            current_task += 1
                            self.progress_update.emit(current_task, total_tasks,
                                                    f"Analyzing {job_name}/{task_name}")

                            if task_name in self.analyzer.config.get('tasks', {}):
                                task_config = self.analyzer.config['tasks'][task_name]
                                job_path = os.path.join(run_path, job_name)
                                task_data = self.analyzer.analyze_task(job_path, task_name, task_config)
                                if task_data:
                                    self.analyzer.analysis_results[run_path]['jobs'][job_name]['tasks'][task_name] = task_data

                        if self._is_running:
                            self.analyzer.analysis_results[run_path]['jobs'][job_name]['summary'] = \
                                self.analyzer.generate_run_summary(
                                    self.analyzer.analysis_results[run_path]['jobs'][job_name]['tasks'])

                    if self._is_running:
                        all_tasks = {}
                        for job_name, job_data in self.analyzer.analysis_results[run_path]['jobs'].items():
                            all_tasks.update(job_data['tasks'])
                        self.analyzer.analysis_results[run_path]['summary'] = \
                            self.analyzer.generate_run_summary(all_tasks)
                        self.analyzer.analysis_results[run_path]['last_updated'] = \
                            datetime.datetime.now().isoformat()

                if self._is_running:
                    self.finished_signal.emit(self.analyzer.analysis_results)

            except Exception as e:
                print(f"ERROR in analysis worker: {e}")
                import traceback
                traceback.print_exc()
                self.finished_signal.emit({})

        def stop(self):
            """Stop the worker gracefully"""
            self._is_running = False
else:
    BackgroundWorker = None
