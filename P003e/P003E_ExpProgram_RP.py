#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 9 2023

Last updated: 2024-01-09

@author: cyruskirkman & Megan C.

This project investigated the roles of various scedules of reinforcement 
(Pavlovian, instrumental, and omission contingencies) in dictating spatial 
and temoporal response variability. It also accounted for proximity to
reinforcement by modifying the number of responses to reach each trial's
outcome; this manipulation occured each phase.

All subjects underwent three phases: RR2, RR5, and RR20 (changed from RR10 after
we found that it was too low). Across each session of each phase, trials could
be one of three types (the reinforcement schedules described above), 
differentiated by stimulus color--nine distinct colors were
counter-balanced across twelve subjects. 

Each trial lasted 10 seconds. Within these 10 s, responses on and off the
presented cue were tracked and could impact the outcome of the trial.
"""
# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
# =============================================================================
from csv import writer, QUOTE_MINIMAL, DictReader
from datetime import datetime, timedelta, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from time import time, sleep
from os import getcwd, popen, mkdir, path as os_path
from random import choice, shuffle
from PIL import ImageTk, Image  

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis.

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        # Import additional libraries...
        import pigpio # import pi, OUTPUT
        import csv
        #...including art scripts
        sys_path.insert(0, str(os_path.expanduser('~')+"/Desktop/Experiments/P033/"))
        import graph
        import polygon_fill
        
        # Setup GPIO numbers (NOT PINS; gpio only compatible with GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21
        
        # Setup use of pi()
        rpi_board = pigpio.pi()
        
        # Then set each pin to output 
        rpi_board.set_mode(servo_GPIO_num,
                           pigpio.OUTPUT) # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num,
                           pigpio.OUTPUT) # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num,
                           pigpio.OUTPUT) # House light LED...
        
        # Setup the servo motor 
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    50) # Default frequency is 50 MhZ
        
        # Next grab the up/down 
        hopper_vals_csv_path = str(os_path.expanduser('~')+"/Desktop/Box_Info/Hopper_vals.csv")
        
        # Store the proper UP/DOWN values for the hopper from csv file
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]
        
        # Lastly, run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
                             
        
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

# Below  is just a safety measure to prevent too many recursive loops). It
# doesn't need to be changed.
setrecursionlimit(5000)

"""
The code below jumpstarts the loop by first building the hopper object and 
making sure everything is turned off, then passes that object to the
control_panel. The program is largely recursive and self-contained within each
object, and a macro-level overview is:
    
    ControlPanel -----------> MainScreen ------------> PaintProgram
         |                        |                         |
    Collects main           Runs the actual         Gets passed subject
    variables, passes      experiment, saves        name, but operates
    to Mainscreen          data when exited          independently
    

"""

# The first of two objects we declare is the ExperimentalControlPanel (CP). It
# exists "behind the scenes" throughout the entire session, and if it is exited,
# the session will terminate.
class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # First, setup the data directory in "Documents"
        self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
        # Next up, we need to do a couple things that will be different based
        # on whether the program is being run in the operant boxes or on a 
        # personal computer. These include setting up the hopper object so it 
        # can be referenced in the future, or the location where data files
        # should be stored.
        if operant_box_version:
            # Setup the data directory in "Documents"
            self.data_folder = "P003e_data" # The folder within Documents where subject data is kept
            self.data_folder_directory = str(os_path.expanduser('~'))+"/Desktop/Data/" + self.data_folder
        else: # If not, just save in the current directory the program us being run in 
            self.data_folder_directory = getcwd() + "/data"
        
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P003e Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Jagger", "Bowie", "Zappa", "Evaristo",
                                 "Meat Loaf", "Herriot", "Hendrix", "Iggy",
                                 "Jubilee", "Kurt", "Sting", "Joplin"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()

        
        # Exp phases
        self.experimental_phase_titles = ["RR2", "RR5", "RR20"]
        
        Label(self.control_window, text="Experimental Phase:").pack()
        self.exp_phase_variable = StringVar(self.control_window)
        self.exp_phase_variable.set("Select")
        self.exp_phase_menu = OptionMenu(self.control_window,
                                          self.exp_phase_variable,
                                          *self.experimental_phase_titles
                                          ).pack()
        
        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
        
    def set_pigeon_ID(self, pigeon_name):
        # This function checks to see if a pigeon's data folder currently 
        # exists in the respective "data" folder within the Documents
        # folder and, if not, creates one.
        try:
            if not os_path.isdir(self.data_folder_directory + pigeon_name):
                mkdir(os_path.join(self.data_folder_directory, pigeon_name))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
        except FileExistsError:
            print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")
                
                
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            if self.exp_phase_variable.get() != "Select":
                print("Operant Box Screen Built") 
                self.MS = MainScreen(
                    str(self.subject_ID_variable.get()), # subject_ID
                    self.record_data_variable.get(), # Boolean for recording data (or not)
                    self.data_folder_directory, # directory for data folder
                    self.exp_phase_variable.get(), # Exp phase name
                    self.experimental_phase_titles.index(self.exp_phase_variable.get()) # Exp Phase number (0 through 2; 0-RR2, 1-RR5, 2-RR20)
                    )
            else:
                print("\n ERROR: Input Stimulus Set Before Starting Session")
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")
            

# Then, setup the MainScreen object
class MainScreen(object):
    # First, we need to declare several functions that are 
    # called within the initial __init__() function that is 
    # run when the object is first built:
    
    def __init__(self, subject_ID, record_data, data_folder_directory,
                 exp_phase_name, exp_phase_num):
        ## Firstly, we need to set up all the variables passed from within
        # the control panel object to this MainScreen object. We do this 
        # by setting each argument as "self." objects to make them global
        # within this object.
        
        # Setup experimental phase
        self.exp_phase_name = exp_phase_name # e.g., "RR2"
        self.exp_phase_num = exp_phase_num # e.g., 0 (0 through 2; 0-RR2, 1-RR5, 2-RR20)
        
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        
        ## Set up the visual Canvas
        self.root = Toplevel()
        self.root.title(f"P003e {self.exp_phase_name}: Spatial Variability") # this is the title of the window
        self.mainscreen_height = 768 # height of the experimental canvas screen
        self.mainscreen_width = 1024 # width of the experimental canvas screen
        self.root.bind("<Escape>", self.exit_program) # bind exit program to the "esc" key
        
        # If the version is the one running in the boxes...
        if operant_box_version: 
            # Keybind relevant keys
            self.cursor_visible = True # Cursor starts on...
            self.change_cursor_state() # turn off cursor UNCOMMENT
            self.root.bind("<c>",
                           lambda event: self.change_cursor_state()) # bind cursor on/off state to "c" key
            # Then fullscreen (on a 1024x768p screen). Assumes that both screens
            # that are being used have identical dimensions
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  1024x768p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()
        
        # Timing variables
        self.start_time = datetime.now()  # This will be reset once the session actually starts
        self.trial_start = datetime.now() # Duration into each trial as a second count, resets each trial
        self.ITI_duration = 6000 # duration of inter-trial interval (ms)
        self.trial_timer_duration = 10000 # Duration of each trial (ms)
        self.current_trial_counter = 0 # counter for current trial in session
        self.trial_stage = 0 # Trial substage (4 within DMTO)
        # Selective hopper timing by subject...
        if self.subject_ID in ["Joplin", "Evaristo"]:
            self.hopper_duration = 5000 # duration of accessible hopper(ms)
        elif self.subject_ID == "Meat Loaf":
            self.hopper_duration = 7000 # duration of accessible hopper(ms)
        if self.subject_ID in ["Herriot", "Jubilee"]:
            self.hopper_duration = 3000 # duration of accessible hopper(ms)
        else:
            self.hopper_duration = 4000 # duration of accessible hopper(ms)

        # These are additional "under the hood" variables that need to be declared
        self.max_trials = 180 # Max number of trials within a session
        self.session_data_frame = [] #This where trial-by-trial data is stored
        self.current_trial_counter = 0 # This counts the number of trials that have passed
        header_list = ["SessionTime", "Xcord","Ycord", "Event", "TrialTime", 
                       "TrialType","TargetPeckNum", "BackgroundPeckNum",
                       "TrialNum", "TrialColor", "Subject", "ExpPhase",
                       "Date", "HiddenPatch"] # Column headers
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)

        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()

    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        
        def first_ITI(event):
            # Is initial delay before first trial starts. It first deletes all the
            # objects off the mnainscreen (making it blank), unbinds the spacebar to 
            # the first_ITI link, followed by a 30s pause before the first trial to 
            # let birds settle in and acclimate.
            print("Spacebar pressed -- SESSION STARTED") 
            self.mastercanvas.delete("all")
            self.root.unbind("<space>")
            self.start_time = datetime.now() # Set start time
            self.trial_cue_color = None
            self.trial_type = "NA"
            
            # First set up the path to the stimulus identity .csv document
            stimuli_csv_path = getcwd() + "/P003E_stimuli_assignments.csv"
                
            # Import the used sample stimuli, their respective key assignments,
            # and conditional assignments as a lists of dictionaries that are 
            # structured as {'Name': 'C2_Phase1.bmp', 'Key': 'L', 'Group': 'E'}. 
            # The list will be equal to the number of elements in the .csv file
            # and doesn't actually take into account any of the literal files.
            with open(stimuli_csv_path, 'r', encoding='utf-8-sig') as f:
                dict_reader = DictReader(f) 
                all_stimulus_assignment_list = list(dict_reader)
        
            
            # After that, let's just pick out the stimuli for a single subject
            for d in all_stimulus_assignment_list:
                if d["Subject"] == self.subject_ID:
                    all_stimulus_assignments_dict = d
                    
            # Next, pick out the specific stimuli colors for that specific 
            # subject and phase. We can do this by making a dictionary of three
            # entries for each bird: one for PAV, INS, and OMS
            self.stimulus_assignments_dict = {}
            for entry in all_stimulus_assignments_dict:
                if entry.split("_")[0] == self.exp_phase_name:
                    self.stimulus_assignments_dict[entry.split("_")[1]] = all_stimulus_assignments_dict[entry]

            # Once we have the three stimuli colors for each bird and phase,
            # we can order all the trials within a session. These should be
            # quasi-randomly ordered, such that there were no more than three 
            # of a single cue across consecutive trials (e.g., never PAV, PAV,
            # PAV, PAV).
            potential_trial_assignments = ["PAV", "INS", "OMS"] * (self.max_trials // 3) # This will be shuffled around...
            self.trial_assignment_list = []

            while len(self.trial_assignment_list) != self.max_trials:
                shuffle(potential_trial_assignments) # shuffle
                approved = True
                c = 0  # counter
                while c < len(potential_trial_assignments) and approved:
                    if c > 3:
                        a = potential_trial_assignments[c]
                        if a == potential_trial_assignments[c-1] and a == potential_trial_assignments[c-2] and a == potential_trial_assignments[c-3]:
                            approved = False
                            break
                    c += 1
                # If passes with approved still true...
                if approved:
                    for i in potential_trial_assignments:
                        self.trial_assignment_list.append(i)
                    
            # After the order of stimuli per trial is determined, we can start.
            # If running a test session, the duration of intervals can be 
            # lowered significantly to make more efficient
            if self.subject_ID == "TEST": # If test, don't worry about ITI delays
                self.ITI_duration = 1000
                self.hopper_duration = 1000
                self.root.after(1000, self.ITI)
            else:
                self.root.after(30000, self.ITI)


        # The runs first, setting up the spacebar trigger
        self.root.bind("<space>", first_ITI) # bind cursor state to "space" key
        self.mastercanvas.create_text(512,374,
                                      fill="white",
                                      font="Times 25 italic bold",
                                      text=f"P003e \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Experimental Phase: {self.exp_phase_name}")
                
    ## %% ITI
    # Every trial (including the first) "starts" with an ITI. The ITI function
    # does several different things:
    #   1) Checks to see if any session constraints have been reached
    #   2) Resets the hopper and any trial-by-trial variables
    #   3) Increases the trial counter by one
    #   4) Moves on to the next trial after a delay
    # 
    def ITI(self):
        # This function just clear the screen. It will be used a lot in the future, too.
        self.clear_canvas()
        
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "ITI_peck": 
                                       self.write_data(event, event_type))
            
        # This turns all the stimuli off from the previous trial (during the
        # ITI). Needs to happen every ITI.
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num,
                            False) # Turn off the hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_down_val) # Hopper down
            rpi_board.write(house_light_GPIO_num, 
                            False) # Turn off house light
        

        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        if self.current_trial_counter == self.max_trials:
            print("Trial max reached")
            self.exit_program("event")
        
        # Else, after a timer move on to the next trial. Note that,
        # although the after() function is given here, the rest of the code 
        # within this function is still executed before moving on.
        else: 
            # Print text on screen if a test (should be black if an experimental trial)
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(512,374,
                                              fill="white",
                                              font="Times 25 italic bold",
                                              text=f"ITI ({int(self.ITI_duration/1000)} sec.)")
                
            # Reset other variables for the following trial.
            self.trial_start = time() # Set trial start time (note that it includes the ITI, which is subtracted later)
            self.trial_peck_counter = 0 # Reset trial peck counter each trial
            self.background_peck_counter = 0 # Also reset background counter
            
            self.write_comp_data(False) # update data .csv with trial data from the previous trial
            
            # First pick the trial type from the prexisting list....
            self.trial_type = self.trial_assignment_list[self.current_trial_counter - 1]
   
            # Increase trial counter by one
            self.current_trial_counter += 1
            
            if self.current_trial_counter == 1:
                self.root.after(self.ITI_duration, self.start_signal_period)
            else:
                # Next, set a delay timer to proceed to the next trial
                self.root.after(self.ITI_duration, self.build_keys)
                
            # Finally, print terminal feedback "headers" for each event within the next trial
            print(f"\n{'*'*30} Trial {self.current_trial_counter} begins {'*'*30}") # Terminal feedback...
            print(f"{'Event Type':>30} | Xcord. Ycord. | Trial | Session Time")
    
        
    #%%  
    """
    This function is called one single time at the very beginning of the
    session. It simply builds a blank square and requires one peck to start 
    the program. This was called to make sure that pigeons were "ready" to 
    start the session, given that trials progressed on a timer. More info
    about building Canvas widgets in the following section.
    """
    def start_signal_period(self):
        # We need to turn on the houselight as soon as the trial starts
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True) # Turn off house light
        # Border...
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        # Make it a button
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event: 
                                       self.background_press(event))
        
        # Next build the actual cue
        key_coord_list =  [416, 288, 608, 480]
        self.mastercanvas.create_rectangle(key_coord_list,
                                      outline = "black",
                                      fill = "white",
                                      tag = "key")

        # Then bind a function to a key press!
        self.mastercanvas.tag_bind("key",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "start_signal_press": 
                                       self.start_signal_press(event, event_type))
            
    def start_signal_press(self, event, event_type):
        # Write data for the peck
        self.write_data(event, event_type)
        self.clear_canvas()
        # Proceed to the first trial after 1 s
        self.root.after(1000, self.build_keys)
        
    
    """
    The code below is very straightforward. It builds the key for the specific
    trial, ties a function to the background and key, and then starts a 10s 
    timer for the trial. Key pecks are incrementally counted and calculated 
    at the end of the timer to see if the criterion is met.
    """
        
    def build_keys(self):
        # Reset trial time as soon as keys are built if 
        if self.current_trial_counter == 1:
            self.trial_start = time() - (self.ITI_duration/1000)# Set trial start time (note that it includes the ITI, which is subtracted later)
        
        # This is a function that builds the all the buttons on the Tkinter
        # Canvas. The Tkinter code (and geometry) may appear a little dense
        # here, but it follows many of the same rules. Al keys will be built
        # during non-ITI intervals, but they will only be filled in and active
        # during specific times. However, pecks to keys will be differentiated
        # regardless of activity.
        
        # We need to turn on the houselight as soon as the trial starts
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True) # Turn off house light
        
        # First, build the background. This basically builds a button the size of 
        # screen to track any pecks; buttons built on top of this button will
        # NOT count as background pecks but as key pecks, because the object is
        # covering that part of the background. Once a peck is made, an event line
        # is appended to the data matrix.
        
        # Border...
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        # Button...
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event: 
                                       self.background_press(event))
        
        # Coordinates for all the keys
        # key_coord_list =  [384, 256, 640, 512]
        key_coord_list =  [416, 288, 608, 480] # 75% = 192 d
        #key_coord_list =  [448, 320, 576, 448] # 50% = 128 d
        midpoint_diameter = 10
        midpoint_coord_list = [
            key_coord_list[0] + ((key_coord_list[2] - key_coord_list[0]) // 2) - (midpoint_diameter//2),
            key_coord_list[1] + ((key_coord_list[3] - key_coord_list[1]) // 2) - (midpoint_diameter//2),
            key_coord_list[0] + ((key_coord_list[2] - key_coord_list[0]) // 2) + (midpoint_diameter//2),
            key_coord_list[1] + ((key_coord_list[3] - key_coord_list[1]) // 2) + (midpoint_diameter//2)
            ]
        
        # Key outline around the key
        outline_size = 20 # 25 pixels in every direction
        outline_coords_list = [
            key_coord_list[0] - outline_size,
            key_coord_list[1] - outline_size,
            key_coord_list[2] + outline_size,
            key_coord_list[3] + outline_size
            ]
        
        # First up, build the actual circle that is the key and will
        # contain the stimulus. Order is important here, as shapes built
        # on top of each other will overlap/cover each other.
        
        self.mastercanvas.create_oval(outline_coords_list, 
                                      outline = "black",
                                      fill = "black",
                                      tag = "key")
        
        self.mastercanvas.create_oval(key_coord_list,
                                      outline = "black",
                                      fill = self.stimulus_assignments_dict[self.trial_type],
                                      tag = "key")
        # Then create the midpoint...
        self.mastercanvas.create_oval(midpoint_coord_list,
                                      fill = "black",
                                      outline = "black",
                                      tag = "key")
        
        # Then bind a function to each key press!
        self.mastercanvas.tag_bind("key",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "key_peck": 
                                       self.key_press(event, event_type))
            
                    
        # Lastly, start a timer for the trial
        self.trial_timer = self.root.after(self.trial_timer_duration,
                                           self.calculate_trial_outcome)
    
    def key_press(self, event, event_type):
        # This is the function that is called whenever a key is pressed. It
        # simply increments the counter and writes a line of data.
        # Add to peck counter
        self.trial_peck_counter += 1
        # Write data for the peck
        self.write_data(event, event_type)
        

    def background_press(self, event):
        # This is the function that is called whenever the background is
        # pressed. It simply increments the counter and writes a line of data.
        # Add to background counter
        self.background_peck_counter += 1
        # Write data for the peck
        self.write_data(event, "background_peck")
        

    def calculate_trial_outcome(self):
        # This function is called once the 10s timer ellapses and calculates
        # whether the trial will be reinforced or not.
        
        self.clear_canvas()
        
        # Always reinforce PAV trials
        if self.trial_type == "PAV":
            reinforced = True
        
        # If INS/OMS trial, reinforcement is probabalistic
        else:
            # Starts out with preset reinforcement ideals...
            if self.trial_type == "INS":
                reinforced = False
            elif self.trial_type == "OMS":
                reinforced = True
            
            # Run a simulation of a dice being rolled...
            rr_sched = int(self.exp_phase_name[2:]) # 2, 5, or 20
            # Roll a die a number of times equal to the number of pecks
            # recorded within that trial
            for iteration in list(range(0, self.trial_peck_counter)): 
                if choice(list(range(0, rr_sched))) == 0:
                    if self.trial_type == "INS":
                        reinforced = True
                    elif self.trial_type == "OMS":
                        reinforced = False
        
        # If a reinforcement is earned...
        if reinforced:
            self.write_data(None, "reinforced_trial")
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(512,374,
                                              fill="white",
                                              font="Times 25 italic bold", 
                                              text=f"Trial Reinforced \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
            
            # Next send output to the box's hardware
            if operant_box_version:
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.write(hopper_light_GPIO_num,
                                True) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_up_val) # Move hopper to up position
            
            self.root.after(self.hopper_duration, lambda: self.ITI())
        
        # If not reinforced, just proceed to the ITI
        else:
            self.write_data(None, "nonreinforced_trial")
            self.ITI()
        
        

    # %% Outside of the main loop functions, there are several additional
    # repeated functions that are called either outside of the loop or 
    # multiple times across phases.
    
    def change_cursor_state(self):
        # This function toggles the cursor state on/off. 
        # May need to update accessibility settings on your machince.
        if self.cursor_visible: # If cursor currently on...
            self.root.config(cursor="none") # Turn off cursor
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else: # If cursor currently off...
            self.root.config(cursor="") # Turn on cursor
            print("### Cursor turned on ###")
            self.cursor_visible = True
    
    def clear_canvas(self):
         # This is by far the most called function across the program. It
         # deletes all the objects currently on the Canvas. A finer point to 
         # note here is that objects still exist onscreen if they are covered
         # up (rendering them invisible and inaccessible); if too many objects
         # are stacked upon each other, it can may be too difficult to track/
         # project at once (especially if many of the objects have functions 
         # tied to them. Therefore, its important to frequently clean up the 
         # Canvas by literally deleting every element.
        try:
            self.mastercanvas.delete("all")
        except TclError:
            print("No screen to exit")
        
    def exit_program(self, event): 
        # This function can be called two different ways: automatically (when
        # time/reinforcer session constraints are reached) or manually (via the
        # "End Program" button in the control panel or bound "esc" key).
            
        # The program does a few different things:
        #   1) Return hopper to down state, in case session was manually ended
        #       during reinforcement (it shouldn't be)
        #   2) Turn cursor back on
        #   3) Writes compiled data matrix to a .csv file 
        #   4) Destroys the Canvas object 
        #   5) Calls the Paint object, which creates an onscreen Paint Canvas.
        #       In the future, if we aren't using the paint object, we'll need 
        #       to 
        def other_exit_funcs():
            if operant_box_version:
                rpi_board.write(hopper_light_GPIO_num,
                                False) # turn off hopper light
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # set hopper to down state
                sleep(1) # Sleep for 1 s
                rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                            False)
                rpi_board.set_PWM_frequency(servo_GPIO_num,
                                            False)
                rpi_board.stop() # Kill RPi board
                
                # root.after_cancel(AFTER)
                if not self.cursor_visible:
                	self.change_cursor_state() # turn cursor back on, if applicable
            self.write_comp_data(True) # write data for end of session
            self.root.destroy() # destroy Canvas
            print("\n GUI window exited")
            
        self.clear_canvas()
        other_exit_funcs()
        print("\n You may now exit the terminal and operater windows now.")
        if operant_box_version:
            polygon_fill.main(self.subject_ID) # call paint object
        
    
    def write_data(self, event, outcome):
            # This function writes a new data line after EVERY peck. Data is
            # organized into a matrix (just a list/vector with two dimensions,
            # similar to a table). This matrix is appended to throughout the 
            # session, then written to a .csv once at the end of the session.
            if event != None: 
                x, y = event.x, event.y
            else: # There are certain data events that are not pecks.
                x, y = "NA", "NA"   
                
            print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_type:^5} | {str(datetime.now() - self.start_time)}")
            # print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | Target: {self.current_target_location: ^2} | {str(datetime.now() - self.start_time)}")
            self.session_data_frame.append([
                str(datetime.now() - self.start_time), # SessionTime as datetime object
                x, # X coordinate of a peck
                y, # Y coordinate of a peck
                outcome, # Type of event (e.g., background peck, target presentation, session end, etc.)
                round((time() - self.trial_start - (self.ITI_duration/1000)), 5), # Time into this trial minus ITI (if session ends during ITI, will be negative)
                self.trial_type, # PAV, INS, OMS
                self.trial_peck_counter, # Count of button pecks that trial
                self.background_peck_counter, # Background peck counter
                self.current_trial_counter, # Trial count within session (1 - max # trials)
                self.stimulus_assignments_dict[self.trial_type], # Trial color
                self.subject_ID, # Name of subject (same across datasheet)
                self.exp_phase_name, # Phase name (e.g., RR2)
                date.today() # Today's date as "MM-DD-YYYY"
                ])
        
            header_list = ["SessionTime", "Xcord","Ycord", "Event", "TrialTime", 
                           "TrialType","TargetPeckNum", "BackgroundPeckNum",
                           "TrialNum", "TrialColor", "Subject", "ExpPhase",
                           "Date"] # Column headers

        
    def write_comp_data(self, SessionEnded):
        # The following function creates a .csv data document. It is either 
        # called after each trial during the ITI (SessionEnded ==False) or 
        # one the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase. Consecutive iterations of the function will simply
        # write over the existing document.
        if SessionEnded:
            self.write_data(None, "SessionEnds") # Writes end of session to df
        if self.record_data : # If experimenter has choosen to automatically record data in seperate sheet:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P003e_data-Phase-{self.exp_phase_name}.csv" # location of written .csv
            # This loop writes the data in the matrix to the .csv              
            edit_myFile = open(myFile_loc, 'w', newline='')
            with edit_myFile as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame) # Write all event/trial data 
            print(f"\n- Data file written to {myFile_loc}")
                
#%% Finally, this is the code that actually runs:
try:   
    if __name__ == '__main__':
        cp = ExperimenterControlPanel()
except:
    # If an unexpected error, make sure to clean up the GPIO board
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                    False)
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    False)
        rpi_board.stop()
