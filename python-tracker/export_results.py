"""
Export evaluation results to Excel with charts and visualizations.
Generates comprehensive evaluation reports with metrics and graphs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from pathlib import Path
from typing import Dict, Optional
import logging
from datetime import datetime
import json

# Excel export
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, LineChart, Reference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationReporter:
    """Generate evaluation reports and export results."""
    
    def __init__(self, output_dir: str = 'evaluation_results'):
        """
        Initialize reporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Define colors for styling
        self.header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        self.header_font = Font(bold=True, color='FFFFFF', size=12)
        self.metric_fill_good = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
        self.metric_fill_warn = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
        self.metric_fill_bad = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    def _get_metric_color(self, value: float, good_threshold: float = 0.7, 
                          warn_threshold: float = 0.5) -> PatternFill:
        """Get color based on metric value."""
        if value >= good_threshold:
            return self.metric_fill_good
        elif value >= warn_threshold:
            return self.metric_fill_warn
        else:
            return self.metric_fill_bad
    
    def export_summary_excel(self, summary_metrics: Dict, output_file: Optional[str] = None):
        """
        Export summary metrics to Excel.
        
        Args:
            summary_metrics: Summary metrics dictionary
            output_file: Output Excel file path
        """
        if output_file is None:
            output_file = str(self.output_dir / 'evaluation_summary.xlsx')
        
        wb = Workbook()
        ws = wb.active
        ws.title = 'Summary'
        
        # Add title
        ws['A1'] = 'Person Detection Evaluation Summary'
        ws['A1'].font = Font(bold=True, size=14, color='FFFFFF')
        ws['A1'].fill = PatternFill(start_color='203864', end_color='203864', fill_type='solid')
        ws.merge_cells('A1:B1')
        ws.row_dimensions[1].height = 25
        
        # Add timestamp
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].font = Font(italic=True, size=10)
        
        # Add metrics
        row = 4
        metrics_data = [
            ('Total Videos', summary_metrics.get('total_videos', 0)),
            ('Total Frames Evaluated', summary_metrics.get('total_frames_evaluated', 0)),
            ('', ''),  # Blank row
            ('Overall Precision', f"{summary_metrics.get('overall_precision', 0):.4f}"),
            ('Overall Recall', f"{summary_metrics.get('overall_recall', 0):.4f}"),
            ('Overall F1 Score', f"{summary_metrics.get('overall_f1_score', 0):.4f}"),
            ('', ''),  # Blank row
            ('True Positives', summary_metrics.get('total_tp', 0)),
            ('False Positives', summary_metrics.get('total_fp', 0)),
            ('False Negatives', summary_metrics.get('total_fn', 0)),
        ]
        
        for metric_name, value in metrics_data:
            if metric_name == '':
                row += 1
                continue
            
            ws[f'A{row}'] = metric_name
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'] = value
            
            # Apply color coding for metric values
            if isinstance(value, str) and '.' in value:
                try:
                    fval = float(value)
                    ws[f'B{row}'].fill = self._get_metric_color(fval)
                except:
                    pass
            
            row += 1
        
        # Adjust columns
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        
        wb.save(output_file)
        logger.info(f"✅ Exported summary to {output_file}")
    
    def export_detailed_results_excel(self, frame_results: pd.DataFrame, 
                                     video_results: Dict,
                                     output_file: Optional[str] = None):
        """
        Export detailed frame-by-frame results to Excel.
        
        Args:
            frame_results: DataFrame with frame-level results
            video_results: Dictionary with per-video results
            output_file: Output Excel file path
        """
        if output_file is None:
            output_file = str(self.output_dir / 'evaluation_detailed.xlsx')
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write frame results
            frame_results.to_excel(writer, sheet_name='Frame Results', index=False)
            
            # Write video summary
            video_summary_data = []
            for video_name, results in video_results.items():
                video_summary_data.append({
                    'Video Name': video_name,
                    'Total Frames': results['total_frames'],
                    'FPS': results['fps'],
                    'Frames Evaluated': len(results['frame_results']),
                    'Precision': results['metrics']['precision'],
                    'Recall': results['metrics']['recall'],
                    'F1 Score': results['metrics']['f1_score'],
                    'TP': results['metrics']['total_tp'],
                    'FP': results['metrics']['total_fp'],
                    'FN': results['metrics']['total_fn'],
                })
            
            df_video_summary = pd.DataFrame(video_summary_data)
            df_video_summary.to_excel(writer, sheet_name='Video Summary', index=False)
        
        # Format Excel file
        wb = load_workbook(output_file)
        
        # Format Frame Results sheet
        ws_frames = wb['Frame Results']
        self._format_worksheet(ws_frames, header_row=1)
        
        # Format Video Summary sheet
        ws_video = wb['Video Summary']
        self._format_worksheet(ws_video, header_row=1)
        
        # Adjust column widths
        for ws in [ws_frames, ws_video]:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length + 2, 30)
        
        wb.save(output_file)
        logger.info(f"✅ Exported detailed results to {output_file}")
    
    def _format_worksheet(self, ws, header_row: int = 1):
        """Apply formatting to worksheet."""
        # Format header row
        for cell in ws[header_row]:
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.border
        
        # Format data rows
        for row in ws.iter_rows(min_row=header_row + 1, max_row=ws.max_row):
            for cell in row:
                cell.border = self.border
                if isinstance(cell.value, float) and 0 <= cell.value <= 1:
                    cell.number_format = '0.0000'
                cell.alignment = Alignment(horizontal='right', vertical='center')
    
    def generate_plots(self, summary_metrics: Dict, video_results: Dict, 
                      frame_results: pd.DataFrame):
        """
        Generate evaluation visualization plots.
        
        Args:
            summary_metrics: Summary metrics dictionary
            video_results: Dictionary with per-video results
            frame_results: DataFrame with frame-level results
        """
        output_file = str(self.output_dir / 'evaluation_plots.pdf')
        
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Overall Metrics Bar Chart
        ax1 = plt.subplot(3, 3, 1)
        metrics = ['Precision', 'Recall', 'F1 Score']
        values = [
            summary_metrics['overall_precision'],
            summary_metrics['overall_recall'],
            summary_metrics['overall_f1_score']
        ]
        colors = ['#2E7D32' if v >= 0.7 else '#F57C00' if v >= 0.5 else '#C62828' for v in values]
        bars = ax1.bar(metrics, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax1.set_ylim([0, 1])
        ax1.set_ylabel('Score', fontweight='bold')
        ax1.set_title('Overall Performance Metrics', fontweight='bold', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. TP, FP, FN Distribution
        ax2 = plt.subplot(3, 3, 2)
        tp_fp_fn = [summary_metrics['total_tp'], summary_metrics['total_fp'], summary_metrics['total_fn']]
        labels = [f"TP\n({summary_metrics['total_tp']})",
                 f"FP\n({summary_metrics['total_fp']})",
                 f"FN\n({summary_metrics['total_fn']})"]
        colors_pie = ['#2E7D32', '#F57C00', '#C62828']
        ax2.pie(tp_fp_fn, labels=labels, colors=colors_pie, autopct='%1.1f%%',
               startangle=90, explode=(0.05, 0.05, 0.05))
        ax2.set_title('Detection Outcomes Distribution', fontweight='bold', fontsize=12)
        
        # 3. Per-Video Performance
        if video_results:
            ax3 = plt.subplot(3, 3, 3)
            video_names = list(video_results.keys())
            f1_scores = [video_results[v]['metrics']['f1_score'] for v in video_names]
            
            bars = ax3.barh(video_names, f1_scores, color='#1976D2', alpha=0.7, edgecolor='black', linewidth=1.5)
            ax3.set_xlim([0, 1])
            ax3.set_xlabel('F1 Score', fontweight='bold')
            ax3.set_title('F1 Score by Video', fontweight='bold', fontsize=12)
            ax3.grid(axis='x', alpha=0.3)
            
            for bar, val in zip(bars, f1_scores):
                width = bar.get_width()
                ax3.text(width, bar.get_y() + bar.get_height()/2.,
                        f' {val:.3f}', ha='left', va='center', fontweight='bold')
        
        # 4. Per-Video Precision
        if video_results:
            ax4 = plt.subplot(3, 3, 4)
            video_names = list(video_results.keys())
            precisions = [video_results[v]['metrics']['precision'] for v in video_names]
            
            ax4.bar(range(len(video_names)), precisions, color='#388E3C', alpha=0.7, edgecolor='black', linewidth=1.5)
            ax4.set_xticks(range(len(video_names)))
            ax4.set_xticklabels(video_names, rotation=45, ha='right')
            ax4.set_ylim([0, 1])
            ax4.set_ylabel('Precision', fontweight='bold')
            ax4.set_title('Precision by Video', fontweight='bold', fontsize=12)
            ax4.grid(axis='y', alpha=0.3)
        
        # 5. Per-Video Recall
        if video_results:
            ax5 = plt.subplot(3, 3, 5)
            video_names = list(video_results.keys())
            recalls = [video_results[v]['metrics']['recall'] for v in video_names]
            
            ax5.bar(range(len(video_names)), recalls, color='#D32F2F', alpha=0.7, edgecolor='black', linewidth=1.5)
            ax5.set_xticks(range(len(video_names)))
            ax5.set_xticklabels(video_names, rotation=45, ha='right')
            ax5.set_ylim([0, 1])
            ax5.set_ylabel('Recall', fontweight='bold')
            ax5.set_title('Recall by Video', fontweight='bold', fontsize=12)
            ax5.grid(axis='y', alpha=0.3)
        
        # 6. Frame-level TP/FP/FN trend
        if not frame_results.empty:
            ax6 = plt.subplot(3, 3, 6)
            ax6.plot(frame_results.index, frame_results['tp'].cumsum(), 
                    marker='o', label='Cumulative TP', color='#2E7D32', linewidth=2, markersize=4)
            ax6.plot(frame_results.index, frame_results['fp'].cumsum(),
                    marker='s', label='Cumulative FP', color='#F57C00', linewidth=2, markersize=4)
            ax6.plot(frame_results.index, frame_results['fn'].cumsum(),
                    marker='^', label='Cumulative FN', color='#C62828', linewidth=2, markersize=4)
            ax6.set_xlabel('Frame', fontweight='bold')
            ax6.set_ylabel('Cumulative Count', fontweight='bold')
            ax6.set_title('Cumulative Detection Outcomes', fontweight='bold', fontsize=12)
            ax6.legend(loc='upper left', fontsize=9)
            ax6.grid(alpha=0.3)
        
        # 7. Mean IoU by Video
        if not frame_results.empty and 'mean_iou' in frame_results.columns:
            ax7 = plt.subplot(3, 3, 7)
            video_names = frame_results['video_name'].unique()
            mean_ious = [frame_results[frame_results['video_name'] == v]['mean_iou'].mean() 
                        for v in video_names]
            
            bars = ax7.bar(range(len(video_names)), mean_ious, color='#7B1FA2', alpha=0.7, edgecolor='black', linewidth=1.5)
            ax7.set_xticks(range(len(video_names)))
            ax7.set_xticklabels(video_names, rotation=45, ha='right')
            ax7.set_ylim([0, 1])
            ax7.set_ylabel('Mean IoU', fontweight='bold')
            ax7.set_title('Mean IoU by Video', fontweight='bold', fontsize=12)
            ax7.grid(axis='y', alpha=0.3)
        
        # 8. Detections vs Annotations by Video
        if not frame_results.empty:
            ax8 = plt.subplot(3, 3, 8)
            video_names = frame_results['video_name'].unique()
            total_detections = [frame_results[frame_results['video_name'] == v]['num_detections'].sum() 
                              for v in video_names]
            total_gts = [frame_results[frame_results['video_name'] == v]['num_ground_truths'].sum() 
                        for v in video_names]
            
            x = np.arange(len(video_names))
            width = 0.35
            ax8.bar(x - width/2, total_detections, width, label='Detections', color='#1976D2', alpha=0.7)
            ax8.bar(x + width/2, total_gts, width, label='Ground Truth', color='#F57C00', alpha=0.7)
            ax8.set_xticks(x)
            ax8.set_xticklabels(video_names, rotation=45, ha='right')
            ax8.set_ylabel('Count', fontweight='bold')
            ax8.set_title('Detections vs Ground Truth', fontweight='bold', fontsize=12)
            ax8.legend()
            ax8.grid(axis='y', alpha=0.3)
        
        # 9. Summary Statistics Table
        ax9 = plt.subplot(3, 3, 9)
        ax9.axis('off')
        
        summary_text = f"""
EVALUATION SUMMARY
{'='*35}
Total Videos: {summary_metrics.get('total_videos', 0)}
Total Frames: {summary_metrics.get('total_frames_evaluated', 0)}

METRICS
{'='*35}
Precision: {summary_metrics.get('overall_precision', 0):.4f}
Recall:    {summary_metrics.get('overall_recall', 0):.4f}
F1 Score:  {summary_metrics.get('overall_f1_score', 0):.4f}

OUTCOMES
{'='*35}
TP: {summary_metrics.get('total_tp', 0)}
FP: {summary_metrics.get('total_fp', 0)}
FN: {summary_metrics.get('total_fn', 0)}
        """
        
        ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"✅ Generated plots: {output_file}")
        plt.close()
    
    def generate_json_report(self, summary_metrics: Dict, video_results: Dict,
                           output_file: Optional[str] = None):
        """
        Generate JSON report for machine-readable format.
        
        Args:
            summary_metrics: Summary metrics dictionary
            video_results: Dictionary with per-video results
            output_file: Output JSON file path
        """
        if output_file is None:
            output_file = str(self.output_dir / 'evaluation_report.json')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary_metrics,
            'per_video': {}
        }
        
        # Convert numpy types to native Python types
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        # Add per-video results
        for video_name, results in video_results.items():
            report['per_video'][video_name] = {
                'fps': float(results['fps']),
                'total_frames': int(results['total_frames']),
                'metrics': convert_types(results['metrics'])
            }
        
        report['summary'] = convert_types(summary_metrics)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Generated JSON report: {output_file}")
    
    def generate_complete_report(self, summary_metrics: Dict, video_results: Dict,
                                frame_results: pd.DataFrame):
        """
        Generate all output files (Excel, plots, JSON).
        
        Args:
            summary_metrics: Summary metrics dictionary
            video_results: Dictionary with per-video results
            frame_results: DataFrame with frame-level results
        """
        logger.info("\n📊 Generating evaluation reports...")
        
        # Export Excel files
        self.export_summary_excel(summary_metrics)
        self.export_detailed_results_excel(frame_results, video_results)
        
        # Generate plots
        self.generate_plots(summary_metrics, video_results, frame_results)
        
        # Generate JSON report
        self.generate_json_report(summary_metrics, video_results)
        
        logger.info(f"\n✅ All reports generated in: {self.output_dir}")
        logger.info(f"   - evaluation_summary.xlsx")
        logger.info(f"   - evaluation_detailed.xlsx")
        logger.info(f"   - evaluation_plots.pdf")
        logger.info(f"   - evaluation_report.json")


if __name__ == '__main__':
    # Example usage
    from evaluate_with_ground_truth import PersonDetectionEvaluator
    from detector import PersonDetector
    from parse_ground_truth import GroundTruthParser
    
    # Run evaluation
    evaluator = PersonDetectionEvaluator(
        detector_class=PersonDetector,
        ground_truth_parser_class=GroundTruthParser,
        video_dir='sample_video/videos/',
        annotations_file='sample_annotations.xlsx'
    )
    
    results = evaluator.evaluate_all_videos(max_frames_per_video=100)
    summary = evaluator.get_summary_metrics()
    frame_results_df = evaluator.get_results_dataframe()
    
    # Generate reports
    reporter = EvaluationReporter()
    reporter.generate_complete_report(summary, results, frame_results_df)
