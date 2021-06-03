import tkinter as tk
from KeithleyGUI import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Plot(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        figure = plt.Figure(figsize=(6,5), dpi=100)
        self.ax = figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.Y, side=tk.LEFT)

if __name__ == "__main__":

# now create gui. First, create the top level frame
    tk_top = tk.Tk()
    tk_top.title("Kiethley")

    tk_left = KeithleyGUI(tk_top)#.pack(side="top", fill="both", expand=True)
    tk_left.pack(side=tk.LEFT, fill=tk.BOTH)

    separator = tk.Frame(tk_top, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

    tk_right = Plot(tk_top)
    tk_right.pack(side=tk.LEFT, fill=tk.BOTH)

    tk_left.setplot(tk_right)

    tk_top.mainloop()

