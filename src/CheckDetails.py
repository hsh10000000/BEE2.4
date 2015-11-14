"""
A widget which displays items in a row with various attributes.

Headings can
be clicked to sort, the item can be enabled/disabled, and info can be shown
via tooltips
"""
from tkinter import ttk
import tkinter as tk

import functools

from tooltip import add_tooltip
import utils
import tk_tools


UP_ARROW = '\u25B3'
DN_ARROW = '\u25BD'

ROW_HEIGHT = 24
ROW_PADDING = 2

style = ttk.Style()
style.configure(
    'CheckDetails.TCheckbutton',
    background='white',
)

class Item:
    """Represents one item in a CheckDetails list.

    """
    def __init__(self, *values):
        self.values = values
        self.state_var = tk.IntVar(value=0)
        self.master = None  # type: CheckDetails
        self.check = None  # type: ttk.Checkbutton
        self.val_widgets = []

    def make_widgets(self, master: 'CheckDetails'):
        if self.master is not None:
            # If we let items move between lists, the old widgets will become
            # orphaned!
            raise ValueError(
                "Can't move Item objects between lists!"
            )

        self.master = master
        self.check = ttk.Checkbutton(
            master.wid_frame,
            variable=self.state_var,
            onvalue=1,
            offvalue=0,
            takefocus=False,
            width=0,
            style='CheckDetails.TCheckbutton',
            command=self.master.update_allcheck,
        )

        self.val_widgets = [
            tk.Label(
                master.wid_frame,
                text=value,
                justify=tk.LEFT,
                anchor=tk.W,
                background='white',
            )
            for value in
            self.values
        ]

    def place(self, check_width, head_pos, y):
        """Position the widgets on the frame."""
        self.check.place(
            x=0,
            y=y,
            width=check_width,
            height=ROW_HEIGHT,
        )
        for widget, (x, width) in zip(self.val_widgets, head_pos):
            widget.place(
                x=x+check_width,
                y=y,
                width=width,
                height=ROW_HEIGHT,
            )
            x += width

    @property
    def state(self) -> bool:
        return self.state_var.get()

    @state.setter
    def state(self, value: bool):
        self.state_var.set(value)
        self.master.update_allcheck()


class CheckDetails(ttk.Frame):
    def __init__(self, parent, items=(), headers=()):
        super(CheckDetails, self).__init__(parent)

        self.parent = parent
        self.headers = list(headers)
        self.items = []
        self.sort_ind = None
        self.rev_sort = False  # Should we sort in reverse?

        self.head_check_var = tk.IntVar(value=False)
        self.wid_head_check = ttk.Checkbutton(
            self,
            variable=self.head_check_var,
            command=self.toggle_allcheck,
            takefocus=False,
            width=0,
        )
        self.wid_head_check.grid(row=0, column=0)

        add_tooltip(
            self.wid_head_check,
            "Toggle all checkboxes."
        )

        def checkbox_enter(e):
            """When hovering over the 'all' checkbox, highlight the others."""
            for item in self.items:
                item.check.state(['active'])
        self.wid_head_check.bind('<Enter>', checkbox_enter)

        def checkbox_leave(e):
            for item in self.items:
                item.check.state(['!active'])
        self.wid_head_check.bind('<Leave>', checkbox_leave)

        self.wid_header = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED,
            sashpad=2,
            showhandle=False,
        )
        self.wid_header.grid(row=0, column=1, sticky='EW')
        self.wid_head_frames = [0] * len(self.headers)
        self.wid_head_label = [0] * len(self.headers)
        self.wid_head_sort = [0] * len(self.headers)
        self.make_headers()

        self.wid_canvas = tk.Canvas(
            self,
        )
        self.wid_canvas.grid(row=1, column=0, columnspan=2, sticky='NSEW')
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.horiz_scroll = tk_tools.HidingScroll(
            self,
            orient=tk.HORIZONTAL,
            command=self.wid_canvas.xview,
        )
        self.vert_scroll = tk_tools.HidingScroll(
            self,
            orient=tk.VERTICAL,
            command=self.wid_canvas.yview,
        )
        self.wid_canvas['xscrollcommand'] = self.horiz_scroll.set
        self.wid_canvas['yscrollcommand'] = self.vert_scroll.set

        self.horiz_scroll.grid(row=2, column=0, columnspan=2, sticky='EWS')
        self.vert_scroll.grid(row=1, column=2, sticky='NSE')
        if utils.USE_SIZEGRIP:
            ttk.Sizegrip(self).grid(row=2, column=2)

        self.wid_frame = tk.Frame(
            self.wid_canvas,
            relief=tk.SUNKEN,
            background='white',
        )
        self.wid_canvas.create_window(0, 0, window=self.wid_frame, anchor='nw')

        self.bind('<Configure>', self.refresh)
        self.bind('<Map>', self.refresh)  # When added to a window, refresh

        self.wid_header.bind('<ButtonRelease-1>', self.refresh)
        self.wid_header.bind('<B1-Motion>', self.refresh)
        self.wid_header.bind('<Configure>', self.refresh)

        for item in items:
            self.add_item(item)

    def make_headers(self):
        """Generate the heading widgets."""

        for i, head_text in enumerate(self.headers):
            self.wid_head_frames[i] = header = ttk.Frame(
                self.wid_header,
                relief=tk.RAISED,
            )

            self.wid_head_label[i] = label = ttk.Label(
                header,
                text=head_text,
            )
            self.wid_head_sort[i] = sorter = ttk.Label(
                header,
                text='',
            )
            label.grid(row=0, column=0, sticky='EW')
            sorter.grid(row=0, column=1, sticky='E')
            header.columnconfigure(0, weight=1)
            self.wid_header.add(header)

            def header_enter(_, label=label, sorter=sorter):
                label['background'] = 'lightblue'
                sorter['background'] = 'lightblue'

            def header_leave(_, label=label, sorter=sorter):
                label['background'] = ''
                sorter['background'] = ''

            header.bind('<Enter>', header_enter)
            header.bind('<Leave>', header_leave)
            utils.bind_leftclick(label, functools.partial(self.sort, i))

            # Headers can't become smaller than their initial size -
            # The amount of space to show all the text + arrow
            header.update_idletasks()
            self.wid_header.paneconfig(
                header,
                minsize=header.winfo_reqwidth(),
            )

            sorter['text'] = ''

    def add_item(self, item):
        self.items.append(item)
        item.make_widgets(self)

    def rem_item(self, item):
        self.items.remove(item)

    def update_allcheck(self):
        """Update the 'all' checkbox to match the state of sub-boxes."""
        num_checked = sum(item.state for item in self.items)
        if num_checked == 0:
            self.head_check_var.set(False)
        elif num_checked == len(self.items):
            self.wid_head_check.state(['!alternate'])
            self.head_check_var.set(True)
            self.wid_head_check.state(['!alternate'])
        else:
            # The 'half' state is just visual.
            # Set to true so everything is blanked when next clicking
            self.head_check_var.set(True)
            self.wid_head_check.state(['alternate'])

    def toggle_allcheck(self):
        value = self.head_check_var.get()
        for item in self.items:
            # Bypass the update function
            item.state_var.set(value)

    def refresh(self, _=None):
        """Reposition the widgets.

        Must be called when self.items is changed,
        or when window is resized.
        """
        self.wid_header.update_idletasks()
        header_sizes = [
            (head.winfo_x(), head.winfo_width())
            for head in
            self.wid_head_frames
        ]

        self.wid_head_check.update_idletasks()
        check_width = self.wid_head_check.winfo_width()
        pos = ROW_PADDING
        for item in self.items:
            item.place(check_width, header_sizes, pos)
            pos += ROW_HEIGHT + ROW_PADDING

        self.wid_frame['width'] = width = max(
            self.wid_canvas.winfo_width(),
            sum(header_sizes[-1]) + check_width,
        )
        self.wid_frame['height'] = height = max(
            self.wid_canvas.winfo_height(),
            pos,
        )

        # Set the size of the canvas
        self.wid_frame.update_idletasks()

        self.wid_canvas['scrollregion'] = (0, 0, width, height)

    def sort(self, index, _=None):
        """Click event for headers."""
        if self.sort_ind is not None:
            self.wid_head_sort[self.sort_ind]['text'] = ''
        if self.sort_ind == index:
            self.rev_sort = not self.rev_sort
        else:
            self.rev_sort = False

        self.wid_head_sort[index]['text'] = (
                UP_ARROW if self.rev_sort else DN_ARROW
            )
        self.sort_ind = index

        self.items.sort(
            key=lambda item: item.values[index],
            reverse=self.rev_sort,
        )
        self.refresh()


if __name__ == '__main__':
    root = tk_tools.TK_ROOT
    test_inst = CheckDetails(
        parent=root,
        headers=['Name', 'Author', 'Description'],
        items=[
            Item('Item1', 'Auth1', 'Blah blah blah'),
            Item('Item5', 'Auth3', 'Lorem Ipsum'),
            Item('Item3', 'Auth2', '.........'),
            Item('Item4', 'Auth2', '.........'),
            Item('Item6', 'Auth4', '.....'),
            Item('Item2', 'Auth1', '...'),
        ]
    )
    test_inst.grid(sticky='NSEW')
    utils.add_mousewheel(test_inst.wid_canvas, root)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.deiconify()
    root.mainloop()