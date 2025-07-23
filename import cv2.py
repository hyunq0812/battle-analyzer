import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class VideoROISelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Selection and Dual ROI Specification")

        self.video_path = None
        self.roi1 = None  # (x, y, w, h) for Trillion units (조 단위)
        self.roi2 = None  # (x, y, w, h) for Hundred Million units (억 단위)
        self.current_roi_drawing = None # Stores (x0, y0, x1, y1) while drawing a rectangle
        # State: 0: Select Video, 1: Draw ROI1 (Trillion), 2: Draw ROI2 (Hundred Million), 3: Ready to Process
        self.current_roi_step = 0 

        self.frame_for_roi = None # The frame displayed for ROI selection
        self.drawing = False      # Flag for mouse drawing
        self.ix, self.iy = -1, -1 # Initial coordinates for drawing

        # UI elements
        self.label_status = tk.Label(self.root, text="Please select a video file.")
        self.label_status.pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack()

        self.btn_select_video = tk.Button(btn_frame, text="Select Video File", command=self.select_video)
        self.btn_select_video.grid(row=0, column=0, padx=5, pady=5)

        self.btn_confirm_roi = tk.Button(btn_frame, text="Confirm ROI", command=self.confirm_current_roi, state='disabled')
        self.btn_confirm_roi.grid(row=0, column=1, padx=5, pady=5)

        self.btn_redraw_roi = tk.Button(btn_frame, text="Redraw Current ROI", command=self.redraw_current_roi, state='disabled')
        self.btn_redraw_roi.grid(row=0, column=2, padx=5, pady=5)

        self.btn_process = tk.Button(btn_frame, text="Start Processing", command=self.process_video, state='disabled')
        self.btn_process.grid(row=0, column=3, padx=5, pady=5)

        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack()

        self.root.mainloop()

    def select_video(self):
        """Opens a file dialog to select a video file."""
        path = filedialog.askopenfilename(title="Select Video File",
                                          filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")])
        if not path:
            return
        self.video_path = path
        self.show_frame_for_roi() # Display a frame from the selected video
        self.current_roi_step = 1 # Move to the first ROI drawing step
        self.update_ui_state()    # Update UI based on the new state

    def show_frame_for_roi(self):
        """Reads and displays a frame from the video for ROI selection."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open video file.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get a frame from roughly 10% into the video, but not more than 60 seconds in
        # This helps in getting a frame where damage numbers are likely visible.
        target_sec = min(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps * 0.1, 60)
        target_frame_no = int(fps * target_sec)

        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_no if target_frame_no < frame_count else 0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("Error", "Could not read frame for ROI selection.")
            return

        self.frame_for_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert BGR to RGB for PIL
        self.display_frame_for_roi()

    def display_frame_for_roi(self):
        """Displays the current frame on the Tkinter canvas."""
        self.canvas.delete("all") # Clear previous drawings
        self.img = Image.fromarray(self.frame_for_roi)
        self.tkimg = ImageTk.PhotoImage(self.img)

        self.canvas.config(width=self.tkimg.width(), height=self.tkimg.height())
        self.canvas.create_image(0, 0, anchor="nw", image=self.tkimg)

        # Draw existing ROIs if they are set
        if self.roi1:
            x, y, w, h = self.roi1
            self.canvas.create_rectangle(x, y, x + w, y + h, outline='blue', width=2, tag="roi1_rect")
        if self.roi2:
            x, y, w, h = self.roi2
            self.canvas.create_rectangle(x, y, x + w, y + h, outline='green', width=2, tag="roi2_rect")

        # Bind mouse events for drawing
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def on_mouse_down(self, event):
        """Handles mouse button press event for drawing."""
        if self.current_roi_step not in [1, 2]: # Only allow drawing if in ROI selection step
            return
        self.drawing = True
        self.ix, self.iy = event.x, event.y
        self.canvas.delete("current_rect") # Clear previous temporary rectangle

    def on_mouse_move(self, event):
        """Handles mouse motion event while drawing."""
        if not self.drawing:
            return
        self.canvas.delete("current_rect") # Redraw rectangle as mouse moves
        self.canvas.create_rectangle(self.ix, self.iy, event.x, event.y, outline='red', width=2, tag="current_rect")

    def on_mouse_up(self, event):
        """Handles mouse button release event after drawing."""
        if not self.drawing:
            return
        self.drawing = False
        x0, y0 = min(self.ix, event.x), min(self.iy, event.y)
        x1, y1 = max(self.ix, event.x), max(self.iy, event.y)
        
        # Store the drawn rectangle coordinates temporarily
        self.current_roi_drawing = (x0, y0, x1 - x0, y1 - y0)
        self.update_ui_state() # Enable Confirm ROI button

    def confirm_current_roi(self):
        """Confirms the currently drawn ROI and moves to the next step."""
        if self.current_roi_drawing is None:
            messagebox.showwarning("Warning", "Please draw an ROI first.")
            return

        if self.current_roi_step == 1:
            self.roi1 = self.current_roi_drawing
            self.canvas.delete("current_rect") # Remove temporary red rectangle
            # Draw the confirmed ROI in blue
            self.canvas.create_rectangle(self.roi1[0], self.roi1[1], self.roi1[0] + self.roi1[2], self.roi1[1] + self.roi1[3], outline='blue', width=2, tag="roi1_rect")
            self.current_roi_step = 2 # Move to drawing ROI2
            self.current_roi_drawing = None # Reset for next drawing
        elif self.current_roi_step == 2:
            self.roi2 = self.current_roi_drawing
            self.canvas.delete("current_rect") # Remove temporary red rectangle
            # Draw the confirmed ROI in green
            self.canvas.create_rectangle(self.roi2[0], self.roi2[1], self.roi2[0] + self.roi2[2], self.roi2[1] + self.roi2[3], outline='green', width=2, tag="roi2_rect")
            self.current_roi_step = 3 # Ready to process
            self.current_roi_drawing = None # Reset for next drawing
        
        self.update_ui_state() # Update UI based on the new state

    def redraw_current_roi(self):
        """Allows redrawing the current ROI."""
        self.canvas.delete("current_rect") # Clear any temporary drawing
        if self.current_roi_step == 1:
            self.canvas.delete("roi1_rect") # Clear the confirmed ROI1 drawing
            self.roi1 = None
        elif self.current_roi_step == 2:
            self.canvas.delete("roi2_rect") # Clear the confirmed ROI2 drawing
            self.roi2 = None
        self.current_roi_drawing = None # Reset the drawn ROI
        self.update_ui_state() # Update UI to reflect redraw state


    def update_ui_state(self):
        """Updates the state of UI elements (buttons, labels) based on current_roi_step."""
        # Reset all button states to disabled by default
        self.btn_select_video.config(state='normal') # Always allow selecting a new video
        self.btn_confirm_roi.config(state='disabled')
        self.btn_redraw_roi.config(state='disabled')
        self.btn_process.config(state='disabled')

        if self.current_roi_step == 0:
            self.label_status.config(text="Please select a video file.")
        elif self.current_roi_step == 1:
            self.label_status.config(text="Please draw the ROI for Trillion units (blue rectangle).")
            if self.current_roi_drawing: # If an ROI has been drawn
                self.btn_confirm_roi.config(state='normal', text="Confirm Trillion ROI")
            self.btn_redraw_roi.config(state='normal', text="Redraw Trillion ROI")
        elif self.current_roi_step == 2:
            self.label_status.config(text="Please draw the ROI for Hundred Million units (green rectangle).")
            if self.current_roi_drawing: # If an ROI has been drawn
                self.btn_confirm_roi.config(state='normal', text="Confirm Hundred Million ROI")
            else:
                self.btn_confirm_roi.config(state='disabled') # Disable if nothing drawn yet
            self.btn_redraw_roi.config(state='normal', text="Redraw Hundred Million ROI")
        elif self.current_roi_step == 3:
            self.label_status.config(text="Both ROIs are set. Click 'Start Processing' to extract images.")
            self.btn_process.config(state='normal')
            self.btn_confirm_roi.config(state='disabled') # No more ROIs to confirm
            self.btn_redraw_roi.config(state='normal', text="Redraw Last ROI") # Allow redrawing the last one if needed

    def process_video(self):
        """Processes the video, crops frames based on selected ROIs, and saves them."""
        if self.video_path is None:
            messagebox.showwarning("Warning", "Please select a video first.")
            return
        if self.roi1 is None or self.roi2 is None:
            messagebox.showwarning("Warning", "Please specify both ROI areas.")
            return
        
        x1, y1, w1, h1 = self.roi1
        x2, y2, w2, h2 = self.roi2

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open video file.")
            return

        # Create separate directories for each ROI's cropped frames
        save_dir_trillion = os.path.join(os.getcwd(), "cropped_frames_trillion")
        save_dir_hundred_million = os.path.join(os.getcwd(), "cropped_frames_hundred_million")
        
        os.makedirs(save_dir_trillion, exist_ok=True)
        os.makedirs(save_dir_hundred_million, exist_ok=True)

        frame_idx = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Starting to process {total_frames} frames...")

        while True:
            ret, frame = cap.read()
            if not ret: # End of video
                break

            # Crop and save Trillion ROI
            cropped_trillion = frame[y1:y1+h1, x1:x1+w1]
            save_path_trillion = os.path.join(save_dir_trillion, f"frame_{frame_idx:05d}.png")
            cv2.imwrite(save_path_trillion, cropped_trillion)

            # Crop and save Hundred Million ROI
            cropped_hundred_million = frame[y2:y2+h2, x2:x2+w2]
            save_path_hundred_million = os.path.join(save_dir_hundred_million, f"frame_{frame_idx:05d}.png")
            cv2.imwrite(save_path_hundred_million, cropped_hundred_million)

            if frame_idx % 50 == 0:  # Print progress every 50 frames (adjustable)
                print(f"[Processing] {frame_idx+1} / {total_frames} frames saved.")

            frame_idx += 1

        cap.release()
        print(f"Completed: Total {frame_idx} ROI images saved to '{save_dir_trillion}' and '{save_dir_hundred_million}'.")
        messagebox.showinfo("Complete", f"Total {frame_idx} ROI images saved to:\n'{save_dir_trillion}'\n'{save_dir_hundred_million}'")

if __name__ == "__main__":
    VideoROISelector()
