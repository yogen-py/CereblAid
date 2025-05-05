import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import time

# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5)

# Game settings
GRID_SIZE = 5  # 5x5 grid
TARGET_COLOR = "red"
BACKGROUND_COLOR = "white"
HIGHLIGHT_COLOR = "blue"
TOTAL_TARGETS = 5  # Total number of targets to hit before ending the game

class EyeControlGridGame:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-fullscreen", True)  # Full-screen mode
        self.root.bind("<Escape>", lambda e: self.quit_game())  # Exit on Esc

        # Game variables
        self.grid_size = GRID_SIZE
        self.target_position = (0, 0)
        self.highlighted_position = None

        # Create canvas for the game grid
        self.canvas = tk.Canvas(self.root, bg=BACKGROUND_COLOR)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create floating camera feed
        self.camera_window = tk.Toplevel(self.root)
        self.camera_window.geometry("300x300+10+10")  # Small floating window
        self.camera_window.overrideredirect(True)  # No title bar
        self.camera_window.attributes("-topmost", True)  # Stay on top
        self.camera_window.bind("<B1-Motion>", self.drag_window)  # Dragging feature

        self.video_frame = tk.Label(self.camera_window)
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        # Create grid and place initial target
        self.create_grid()
        self.place_target()

        # Initialize camera
        self.cap = cv2.VideoCapture(0)

        # Create metrics label
        self.metrics_label = tk.Label(self.root, text="", font=("Arial", 14), bg="white", anchor="e")
        self.metrics_label.place(relx=0.8, rely=0.02)  # Top-right corner

        # Metrics variables
        self.start_time = time.time()
        self.total_attempts = 0
        self.successful_hits = 0

        self.update_camera()

    def drag_window(self, event):
        """Allow the camera window to be dragged."""
        x = self.camera_window.winfo_x() + event.x
        y = self.camera_window.winfo_y() + event.y
        self.camera_window.geometry(f"+{x}+{y}")

    def create_grid(self):
        """Draw grid cells."""
        self.cell_width = self.canvas.winfo_screenwidth() // self.grid_size
        self.cell_height = self.canvas.winfo_screenheight() // self.grid_size

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x0 = col * self.cell_width
                y0 = row * self.cell_height
                x1 = x0 + self.cell_width
                y1 = y0 + self.cell_height
                self.canvas.create_rectangle(x0, y0, x1, y1, outline="black", tags=f"cell-{row}-{col}")

    def place_target(self):
        """Place target at a random position."""
        row = random.randint(0, self.grid_size - 1)
        col = random.randint(0, self.grid_size - 1)
        self.target_position = (row, col)

        x0 = col * self.cell_width
        y0 = row * self.cell_height
        x1 = x0 + self.cell_width
        y1 = y0 + self.cell_height

        self.canvas.create_rectangle(x0, y0, x1, y1, fill=TARGET_COLOR, outline="black", tags="target")

    def highlight_cell(self, row, col):
        """Highlight a cell based on eye movement."""
        if self.highlighted_position:
            # Remove highlight from previous cell
            prev_row, prev_col = self.highlighted_position
            x0 = prev_col * self.cell_width
            y0 = prev_row * self.cell_height
            x1 = x0 + self.cell_width
            y1 = y0 + self.cell_height
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=BACKGROUND_COLOR, outline="black", tags=f"cell-{prev_row}-{prev_col}")

        # Highlight the new cell
        x0 = col * self.cell_width
        y0 = row * self.cell_height
        x1 = x0 + self.cell_width
        y1 = y0 + self.cell_height
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=HIGHLIGHT_COLOR, outline="black", tags=f"cell-{row}-{col}")
        self.highlighted_position = (row, col)

        # Check if the highlighted cell matches the target
        self.total_attempts += 1
        if (row, col) == self.target_position:
            self.successful_hits += 1
            self.canvas.delete("target")
            if self.successful_hits >= TOTAL_TARGETS:
                self.end_game()
            else:
                self.place_target()

        self.update_metrics()

    def update_metrics(self):
        """Update and display metrics on the UI."""
        elapsed_time = time.time() - self.start_time
        accuracy = (self.successful_hits / self.total_attempts) * 100 if self.total_attempts > 0 else 0

        metrics_text = (f"Accuracy: {accuracy:.2f}%  |  Time: {elapsed_time:.2f} sec  |  "
                        f"Speed: {self.successful_hits / elapsed_time:.2f} hits/sec" if elapsed_time > 0 else "")
        self.metrics_label.config(text=metrics_text)

    def update_camera(self):
        """Capture video feed and process eye movements."""
        success, frame = self.cap.read()
        if not success:
            print("Failed to grab frame.")
            self.quit_game()
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark

                # Eye control logic
                img_height, img_width, _ = frame.shape
                left_eye = landmarks[362]  # Left eye center
                right_eye = landmarks[133]  # Right eye center
                eye_x = int((left_eye.x + right_eye.x) / 2 * self.grid_size)
                eye_y = int((left_eye.y + right_eye.y) / 2 * self.grid_size)

                if 0 <= eye_x < self.grid_size and 0 <= eye_y < self.grid_size:
                    self.highlight_cell(eye_y, eye_x)

        # Display the camera feed
        resized_frame = cv2.resize(frame, (300, 300))
        img = Image.fromarray(resized_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_frame.imgtk = imgtk
        self.video_frame.configure(image=imgtk)

        # Schedule next camera update
        self.video_frame.after(10, self.update_camera)

    def end_game(self):
        """End the game and show final performance."""
        elapsed_time = time.time() - self.start_time
        accuracy = (self.successful_hits / self.total_attempts) * 100 if self.total_attempts > 0 else 0
        speed = self.successful_hits / elapsed_time if elapsed_time > 0 else 0

        final_message = (f"Game Over!\n\n"
                         f"Targets Hit: {self.successful_hits}\n"
                         f"Total Attempts: {self.total_attempts}\n"
                         f"Accuracy: {accuracy:.2f}%\n"
                         f"Total Time: {elapsed_time:.2f} sec\n"
                         f"Speed: {speed:.2f} hits/sec")
        messagebox.showinfo("Performance Summary", final_message)
        self.quit_game()

    def quit_game(self):
        """Cleanup resources and close the application."""
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    game = EyeControlGridGame(root)
    root.mainloop()
