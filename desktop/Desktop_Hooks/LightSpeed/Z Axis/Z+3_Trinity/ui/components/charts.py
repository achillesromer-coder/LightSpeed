"""
LightSpeed V0.9.5 - Chart & Visualization Components
Data visualization with modern design

Components:
- ChartCard: Layered card with embedded chart
- StatCard: Single statistic display with icon
- MiniChart: Compact chart for dashboards
- DataTable: Enhanced table view

Author: LightSpeed Team
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Tuple
from .layered_card import LayeredCard


class StatCard(tk.Frame):
    """
    Single statistic display card.

    Features:
    - Large value display
    - Icon/emoji
    - Label
    - Trend indicator (up/down/neutral)
    - Color coding
    """

    def __init__(self, parent, label: str, value: str = "0",
                 icon: str = "", trend: Optional[str] = None, **kwargs):
        """
        Initialize stat card.

        Args:
            parent: Parent widget
            label: Statistic label
            value: Initial value
            icon: Icon/emoji (e.g., "📊", "✓", "⚡")
            trend: Trend indicator ("up", "down", "neutral", None)
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.configure(
            bg='#102040',
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightbackground='#1E3A5F'
        )

        # Icon (if provided)
        if icon:
            tk.Label(
                self,
                text=icon,
                bg='#102040',
                font=('Segoe UI', 20)
            ).pack(pady=(10, 0))

        # Value
        self.value_label = tk.Label(
            self,
            text=value,
            bg='#102040',
            fg='#00FFFF',
            font=('Segoe UI', 20, 'bold')
        )
        self.value_label.pack(pady=(5 if icon else 10, 2))

        # Label
        tk.Label(
            self,
            text=label,
            bg='#102040',
            fg='#88CCFF',
            font=('Segoe UI', 9)
        ).pack(pady=(0, 5))

        # Trend indicator
        if trend:
            trend_symbols = {
                'up': '▲ Up',
                'down': '▼ Down',
                'neutral': '● Stable'
            }
            trend_colors = {
                'up': '#00FF00',
                'down': '#FF3333',
                'neutral': '#88CCFF'
            }
            tk.Label(
                self,
                text=trend_symbols.get(trend, ''),
                bg='#102040',
                fg=trend_colors.get(trend, '#88CCFF'),
                font=('Segoe UI', 8)
            ).pack(pady=(0, 10))

    def set_value(self, value: str):
        """Update statistic value"""
        self.value_label.config(text=value)


class ChartCard(LayeredCard):
    """
    Layered card with embedded chart/graph.

    Extends LayeredCard with chart-specific features.
    """

    def __init__(self, parent, title: str = "", subtitle: str = "",
                 chart_type: str = 'bar', height: int = 300, **kwargs):
        """
        Initialize chart card.

        Args:
            parent: Parent widget
            title: Card title
            subtitle: Card subtitle
            chart_type: Chart type ('bar', 'line', 'pie', 'text')
            height: Card height
            **kwargs: Additional LayeredCard parameters
        """
        super().__init__(parent, title=title, subtitle=subtitle,
                        height=height, elevation=2, **kwargs)

        self.chart_type = chart_type
        self.data = []

        # Chart canvas
        self.chart_canvas = tk.Canvas(
            self.content,
            bg='#0F1F35',
            highlightthickness=0
        )
        self.chart_canvas.pack(fill='both', expand=True, padx=5, pady=5)

        # Bind resize
        self.chart_canvas.bind('<Configure>', self._redraw)

    def set_data(self, data: List[Tuple[str, float]], colors: Optional[List[str]] = None):
        """
        Set chart data and redraw.

        Args:
            data: List of (label, value) tuples
            colors: Optional list of colors for each bar
        """
        self.data = data
        self.colors = colors or ['#00FFFF'] * len(data)
        self._redraw()

    def _redraw(self, event=None):
        """Redraw chart"""
        if not self.data:
            return

        self.chart_canvas.delete('all')
        width = self.chart_canvas.winfo_width()
        height = self.chart_canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        if self.chart_type == 'bar':
            self._draw_bar_chart(width, height)
        elif self.chart_type == 'line':
            self._draw_line_chart(width, height)
        elif self.chart_type == 'text':
            self._draw_text_display(width, height)

    def _draw_bar_chart(self, width: int, height: int):
        """Draw bar chart"""
        if not self.data:
            return

        margin = 40
        chart_width = width - (2 * margin)
        chart_height = height - (2 * margin)

        max_value = max(val for _, val in self.data) if self.data else 1
        bar_width = chart_width / len(self.data) * 0.8

        for i, ((label, value), color) in enumerate(zip(self.data, self.colors)):
            # Bar
            x = margin + (i * chart_width / len(self.data))
            bar_height = (value / max_value) * chart_height if max_value > 0 else 0
            y = height - margin - bar_height

            self.chart_canvas.create_rectangle(
                x, y,
                x + bar_width, height - margin,
                fill=color,
                outline='#1E3A5F'
            )

            # Value label
            self.chart_canvas.create_text(
                x + bar_width / 2, y - 5,
                text=str(int(value)),
                fill='#FFFFFF',
                font=('Segoe UI', 8)
            )

            # X-axis label
            self.chart_canvas.create_text(
                x + bar_width / 2, height - margin + 15,
                text=label,
                fill='#88CCFF',
                font=('Segoe UI', 8),
                angle=0
            )

    def _draw_line_chart(self, width: int, height: int):
        """Draw line chart"""
        if not self.data or len(self.data) < 2:
            return

        margin = 40
        chart_width = width - (2 * margin)
        chart_height = height - (2 * margin)

        max_value = max(val for _, val in self.data)
        points = []

        for i, (label, value) in enumerate(self.data):
            x = margin + (i * chart_width / (len(self.data) - 1))
            y = height - margin - (value / max_value * chart_height if max_value > 0 else 0)
            points.extend([x, y])

            # Data point
            self.chart_canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill='#00FFFF',
                outline='#FFFFFF'
            )

        # Line
        if len(points) >= 4:
            self.chart_canvas.create_line(
                *points,
                fill='#00FFFF',
                width=2,
                smooth=True
            )

    def _draw_text_display(self, width: int, height: int):
        """Draw text-based data display"""
        y_offset = 20
        for label, value in self.data:
            self.chart_canvas.create_text(
                20, y_offset,
                text=f"{label}: {value}",
                fill='#FFFFFF',
                font=('Segoe UI', 10),
                anchor='w'
            )
            y_offset += 25


class MiniChart(tk.Canvas):
    """
    Compact chart for dashboard widgets.

    Features:
    - Small footprint (100x50 typical)
    - Sparkline-style
    - Quick visual trends
    """

    def __init__(self, parent, data: List[float], width=100, height=50, **kwargs):
        """
        Initialize mini chart.

        Args:
            parent: Parent widget
            data: List of values
            width: Canvas width
            height: Canvas height
            **kwargs: Additional Canvas parameters
        """
        super().__init__(parent, width=width, height=height,
                        bg='#0F1F35', highlightthickness=0, **kwargs)

        self.data = data
        self._draw()

    def _draw(self):
        """Draw sparkline"""
        if not self.data or len(self.data) < 2:
            return

        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        margin = 5

        max_val = max(self.data)
        min_val = min(self.data)
        value_range = max_val - min_val if max_val != min_val else 1

        points = []
        for i, value in enumerate(self.data):
            x = margin + (i * (width - 2 * margin) / (len(self.data) - 1))
            y = height - margin - ((value - min_val) / value_range * (height - 2 * margin))
            points.extend([x, y])

        # Line
        if len(points) >= 4:
            self.create_line(*points, fill='#00FFFF', width=1, smooth=True)

    def update_data(self, data: List[float]):
        """Update chart data"""
        self.data = data
        self.delete('all')
        self._draw()


class DataTable(tk.Frame):
    """
    Enhanced table view with sorting and filtering.

    Features:
    - Column headers
    - Sortable columns
    - Row selection
    - Alternating row colors
    """

    def __init__(self, parent, columns: List[str], **kwargs):
        """
        Initialize data table.

        Args:
            parent: Parent widget
            columns: List of column names
            **kwargs: Additional Frame parameters
        """
        super().__init__(parent, **kwargs)

        self.configure(bg='#0A1628')
        self.columns = columns
        self.data = []

        # Table container
        table_container = tk.Frame(self, bg='#0A1628')
        table_container.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(table_container)
        scrollbar.pack(side='right', fill='y')

        # Treeview (table)
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            yscrollcommand=scrollbar.set
        )
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)

        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=100)

        # Style
        style = ttk.Style()
        style.configure("Treeview",
                       background='#0F1F35',
                       foreground='#FFFFFF',
                       fieldbackground='#0F1F35',
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background='#102040',
                       foreground='#FFFFFF',
                       borderwidth=1)

    def set_data(self, data: List[List[Any]]):
        """
        Set table data.

        Args:
            data: List of rows, each row is a list of values
        """
        self.data = data
        self._refresh()

    def _refresh(self):
        """Refresh table display"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add rows
        for row in self.data:
            self.tree.insert('', 'end', values=row)

    def _sort_by(self, column: str):
        """Sort table by column"""
        col_index = self.columns.index(column)

        # Sort data
        self.data.sort(key=lambda row: row[col_index])
        self._refresh()


# Export public API
__all__ = ['ChartCard', 'StatCard', 'MiniChart', 'DataTable']
