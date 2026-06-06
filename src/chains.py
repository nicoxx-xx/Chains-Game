import random
import time
import argparse
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox

def center_figure():
    manager = plt.get_current_fig_manager()
    window = manager.window

    window.update_idletasks()
    window.update()

    #w = window.winfo_width()
    #h = window.winfo_height()

    w = window.winfo_reqwidth()
    h = window.winfo_reqheight()
    ws = window.winfo_screenwidth()
    hs = window.winfo_screenheight()

    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)

    window.geometry(f"{w}x{h}+{x}+{y}")

def print_dictionary(diz):
    print("\nGenerated dictionary:")
    for key, values in diz.items():
        print(f"  {key}: {values}")

def generate_orthogonal_chains(n, m, k):
    """Generates the initial structure of the chains on the grid."""
    to_visit = {(i, j) for i in range(n) for j in range(m)}
    chain_dictionary = {}
    chain_id = 1
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while to_visit:
        current_point = random.choice(list(to_visit))
        current_chain = [current_point]
        to_visit.remove(current_point)
        target_length = random.randint(2, k)

        for _ in range(target_length - 1):
            valid_neighbors = []
            x, y = current_point
            for dx, dy in directions:
                neighbor = (x + dx, y + dy)
                if neighbor in to_visit:
                    valid_neighbors.append(neighbor)
            if not valid_neighbors:
                break
            next_point = random.choice(valid_neighbors)
            current_chain.append(next_point)
            to_visit.remove(next_point)
            current_point = next_point

        if len(current_chain) == 1:
            isolated_point = current_chain[0]
            merged = False
            for c_id, points in chain_dictionary.items():
                for node in [points[0], points[-1]]:
                    distance = abs(isolated_point[0] - node[0]) + abs(isolated_point[1] - node[1])
                    if distance == 1 and len(points) < k:
                        if node == points[0]:
                            points.insert(0, isolated_point)
                        else:
                            points.append(isolated_point)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                chain_dictionary[f"Chain_{chain_id}"] = current_chain
                chain_id += 1
        else:
            chain_dictionary[f"Chain_{chain_id}"] = current_chain
            chain_id += 1
    return chain_dictionary

def verify_free_path(chain_points, selected_end, n, m, chain_dictionary):
    """
    Checks if the selected end is free to exit in the direction of its last segment.
    """
    if len(chain_points) == 1:
        # An isolated point has a free path if at least one side is not blocked
        p = chain_points[0]
        all_occupied = set()
        for c_id, pts in chain_dictionary.items():
            all_occupied.update(pts)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (p[0] + dx, p[1] + dy)
            if neighbor not in all_occupied or not (0 <= neighbor[0] < n and 0 <= neighbor[1] < m):
                return True
        return False

    # Determine exit direction based on selected end
    if selected_end == chain_points[0]:
        current = chain_points[0]
        previous = chain_points[1]
    else:
        current = chain_points[-1]
        previous = chain_points[-2]

    dx = current[0] - previous[0]
    dy = current[1] - previous[1]

    occupied_points = set()
    for c_id, pts in chain_dictionary.items():
        if pts != chain_points:
            occupied_points.update(pts)

    check_x, check_y = current[0] + dx, current[1] + dy
    while 0 <= check_x < n and 0 <= check_y < m:
        if (check_x, check_y) in occupied_points:
            return False
        check_x += dx
        check_y += dy

    return True

def count_free_chains(n, m, chain_dictionary):
    """
    Counts how many chains have at least one free end.
    """
    count = 0
    for c_id, points in chain_dictionary.items():
        start_free = verify_free_path(points, points[0], n, m, chain_dictionary)
        end_free = verify_free_path(points, points[-1], n, m, chain_dictionary)

        if start_free or end_free:
            count += 1

    return count

class InteractiveApplication:
    def __init__(self, n, m, k, dictionary, timer):
        self.n = n
        self.m = m
        self.k = k
        self.dictionary = dictionary
        self.gametimer = timer

        self.fig, self.ax = plt.subplots(figsize=(11, 9.5))

        plt.pause(0.1)
        center_figure()

        plt.subplots_adjust(bottom=0.1)
        self.fig.suptitle("00:00:00", fontsize=12, fontweight='bold', color='green', ha='center', va='top')

        self.base_colors = plt.colormaps['tab20'].resampled(20)
        self.generate_color_map()

        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        ax_button = plt.axes([0.1, 0.02, 0.15, 0.03])
        self.btn_restart = Button(ax_button, 'Restart', color='#f0f0f0', hovercolor='#d0d0d0')
        self.btn_restart.on_clicked(self.on_restart)

        self.fig.text(0.65, 0.03, "(C) Domenico Longo - 2026", ha='left', va='center', fontsize=12, color='blue')

        ax_box_n = plt.axes([0.30, 0.02, 0.05, 0.03])
        ax_box_m = plt.axes([0.40, 0.02, 0.05, 0.03])
        ax_box_k = plt.axes([0.50, 0.02, 0.05, 0.03])

        self.box_n = TextBox(ax_box_n, "n: ", initial=str(n))
        self.box_m = TextBox(ax_box_m, "m: ", initial=str(m))
        self.box_k = TextBox(ax_box_k, "k: ", initial=str(k))

        def validate_numbers(text, box):
            filtered = "".join(c for c in text if c.isdigit() or c == "-")
            if filtered != text:
                box.set_val(filtered)

        self.box_n.on_text_change(lambda t: validate_numbers(t, self.box_n))
        self.box_m.on_text_change(lambda t: validate_numbers(t, self.box_m))
        self.box_k.on_text_change(lambda t: validate_numbers(t, self.box_k))

        """ timer handling """
        self.running = False
        self.start_time = None
        self.elapsed = 0
        self.timer = self.fig.canvas.new_timer(interval=1000)
        self.timer.add_callback(self.update_timer)

        self.update_plot()

    def start_timer(self):
        if self.running: #to handle subsequent start_timer call (off-sequence start/stop)
            self.running = False
            self.timer.stop()
        if not self.running:
            self.elapsed = 0
            self.fig.suptitle("00:00:00", fontsize=12, fontweight='bold', color='green', ha='center', va='top')

            self.running = True
            self.start_time = time.time() - self.elapsed
            self.timer.start()

    def stop_timer(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.elapsed = time.time() - self.start_time

    def update_timer(self):
        if not self.running:
            return

        self.elapsed = time.time() - self.start_time

        h = int(self.elapsed // 3600)
        m = int((self.elapsed % 3600) // 60)
        s = int(self.elapsed % 60)

        self.fig.suptitle(f"{h:02d}:{m:02d}:{s:02d}", fontsize=12, fontweight='bold', color='green', ha='center', va='top')
        self.fig.canvas.draw_idle()
        self.fig.canvas.set_cursor(1)

    def generate_color_map(self):
        """Assigns a unique color to each chain."""
        self.chain_colors = {c_id: self.base_colors(i % 20) for i, c_id in enumerate(self.dictionary.keys())}

    def update_plot(self):
        self.ax.clear()

        for i in range(self.n):
            for j in range(self.m):
                self.ax.plot(j, i, 'o', color='#E0E0E0', markersize=8, zorder=1)

        for c_id, points in self.dictionary.items():
            color = self.chain_colors.get(c_id, '#000000')
            x_coords = [p[1] for p in points]
            y_coords = [p[0] for p in points]

            self.ax.plot(x_coords, y_coords, '-', color=color, linewidth=4, zorder=2)
            self.ax.scatter(x_coords, y_coords, color=color, s=100, zorder=3)

            self.ax.scatter([x_coords[0], x_coords[-1]], [y_coords[0], y_coords[-1]],
                            facecolors='none', edgecolors='gray', linewidths=2, s=150, zorder=4)

        total_remaining = len(self.dictionary)
        free = count_free_chains(self.n, self.m, self.dictionary)

        title_text = f"Click on one end to remove a chain if it has a free path!\nChains remaining: {total_remaining}  |  Available moves: {free}"
        self.ax.set_title(title_text, fontsize=12, pad=15, weight='bold')

        self.ax.set_xlim(-0.5, self.m - 0.5)
        self.ax.set_ylim(-0.5, self.n - 0.5)
        self.ax.set_xticks(range(self.m))
        self.ax.set_yticks(range(self.n))
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.ax.invert_yaxis()
        self.fig.canvas.draw_idle()

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        click_col = int(round(event.xdata))
        click_row = int(round(event.ydata))
        clicked_point = (click_row, click_col)

        chain_to_remove = None

        for c_id, points in self.dictionary.items():
            if clicked_point == points[0] or clicked_point == points[-1]:
                if verify_free_path(points, clicked_point, self.n, self.m, self.dictionary):
                    chain_to_remove = c_id
                    break

        if chain_to_remove:
            print(f"Successfully removed: {chain_to_remove} -> {self.dictionary[chain_to_remove]}")
            del self.dictionary[chain_to_remove]

            free_remaining = count_free_chains(self.n, self.m, self.dictionary)
            print(f"Chains still free in dictionary: {free_remaining}")

            self.update_plot()

            if not self.dictionary:
                print("\nCongratulations! You completely cleared the grid!")
                self.ax.set_title("GRID COMPLETELY CLEARED!", color='green', fontsize=14, weight='bold')
                self.fig.canvas.draw_idle()
                self.stop_timer()
            elif free_remaining == 0:
                print("\nGame Over: No more removable chains!")
                self.ax.set_title("GAME OVER - NO MOVES AVAILABLE!", color='red', fontsize=12, weight='bold')
                self.fig.canvas.draw_idle()
                self.stop_timer()
        else:
            print("Invalid click: the point is not an end or the exit path is blocked.")

    def on_restart(self, event):
        """Triggered by Restart button click."""

        text_n = self.box_n.text
        text_m = self.box_m.text
        text_k = self.box_k.text

        try:
            self.n = int(text_n)
            self.m = int(text_m)
            self.k = int(text_k)

            print(f"Variables have been updated: n={self.n}, m={self.m}, k={self.k}")

        except ValueError:
            print("Error: Enter only integer numeric values!")

        print(f"\nGenerating new game ({self.n}x{self.m}, K={self.k}, TIMER={self.gametimer})...")
        self.dictionary = generate_orthogonal_chains(self.n, self.m, self.k)
        print_dictionary(self.dictionary)
        self.generate_color_map()
        self.update_plot()
        if self.gametimer:
            self.start_timer()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Puzzle Game: Clear the grid of orthogonal chains."
    )

    parser.add_argument("-n", type=int, default=6, help="Number of matrix rows (N)")
    parser.add_argument("-m", type=int, default=8, help="Number of matrix columns (M)")
    parser.add_argument("-k", type=int, default=5, help="Maximum length of each chain (K)")
    parser.add_argument("--timer", action=argparse.BooleanOptionalAction, default=False, help="Enable or disable game timer")

    args = parser.parse_args()

    N = args.n
    M = args.m
    K = args.k
    TIMER = args.timer

    print(f"Matplotlib default graphical backend: ", matplotlib.get_backend())

    print(f"Generating grid {N}x{M} (K={K}, TIMER={TIMER})...")

    initial_data = generate_orthogonal_chains(N, M, K)

    print_dictionary(initial_data)

    print("\nOpening interactive plot...")
    app = InteractiveApplication(N, M, K, initial_data, TIMER)
    if TIMER:
        app.start_timer() # must be called BEFORE plt.show() and after app inizialization
    plt.show()
