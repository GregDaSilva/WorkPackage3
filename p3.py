# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
from time import sleep
import time

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
guess_num = 0
actual_value = 0
Buzz_PWM = None
LED_PWM = None
Num_Guesses = 0
option=None 

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()


# Print the game banner
def welcome():
    os.system('clear')
    print(" _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    global actual_value
    global Num_Guesses
    global guess_num
    global option
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    mode = option
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        print("Guessed number : {}".format(guess_num))
        actual_value = generate_number()
        Num_Guesses = 0

        while not end_of_game:
            pass
        guess_num = 0
        totalRoundGuesses = 0

    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")



def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))

    # print out the scores in the required format
    for i in range(3 if count > 3 else count):
        print("{} - {} took {} guesses".format(i+1, (raw_data[i])[0], (raw_data[i])[1]))

    pass

# Setup Pins
def setup():
    ## DONE
    global Buzz_PWM
    global LED_PWM

    # Setup board mode
    GPIO.setmode(GPIO.BOARD)

    # Setup regular GPIO
    for i in range(len(LED_value)):
        GPIO.setup(LED_value[i], GPIO.OUT)
        GPIO.output(LED_value[i], False)


    GPIO.setup(32, GPIO.OUT)
    GPIO.setup(33, GPIO.OUT)
    GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Setup PWM channels
    Buzz_PWM = GPIO.PWM(33, 1)
    LED_PWM = GPIO.PWM(32, 1000) 

    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)

    pass

# Load high scores
def fetch_scores():
    global eeprom
    ## DONE
    # get however many scores there are
    score_count = eeprom.read_byte(0)
    scores_array = []

    if score_count > 0:
        rawData = eeprom.read_block(1,score_count*4)

        # Get the scores
        for i in range(0, score_count*4, 4):
            playerName = ''

            # convert the codes back to ascii
            for j in range(3):
                playerName += chr(rawData[i+j])

            scores_array.append([playerName, rawData[i + 3]])


    # return back the results
    return score_count, scores_array

# Save high scores
def save_scores(name, new_score):
    global eeprom
    ## DONE
    # fetch scores
    score_count, ss = fetch_scores()

    # include new score
    if not([name, new_score] in ss):
        ss.append([name, new_score])

        # sort
        ss.sort(key=lambda x: x[1])

        # update total amount of scores
        score_count += 1
        eeprom.write_block(0, [4])

        # write new scores
        for i, score in enumerate(ss):
            data_to_write = []
            # get the string
            for k in score[0]:
                data_to_write.append(ord(k))
            data_to_write.append(score[1])
            eeprom.write_block(i+1, data_to_write)
    pass

# Generate guess number
def generate_number():
    ## DONE
    return random.randint(0, pow(2, 3)-1)

# Increase button pressed
def btn_increase_pressed(channel):
    ## DONE
    global guess_num
    global option

    if option != 'P':
        return

    if guess_num == 7:
        guess_num = 0
    else:
        guess_num += 1

    #clearLines()
    print("Guessed number : {}".format(guess_num))

    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess
    
    binLEDs = format(guess_num, '#05b')[2:]
    binLEDs = (bool(int(binLEDs[2])),bool(int(binLEDs[1])),bool(int(binLEDs[0])))
    GPIO.output(tuple(LED_value), binaryLEDs)
    pass

def printState(channel):
    print(GPIO.input(channel))

# Guess button
def btn_guess_pressed(channel):
    global guess_num
    global actual_value
    global LED_PWM
    global Buzz_PWM
    global Num_Guesses
    global mode
    global end_of_game

    if option != 'P':
        return
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    time_pressed = time.time()

    while GPIO.input(channel) == GPIO.LOW:
        time.sleep(0.0001)
    
    time_released = time.time()

    if time_released - time_pressed >= 2:
        #clearLines()
        end_of_game = True
        return
    
    #clearlines()

    print("Confirmed Guess : {}".format(guess_num))

    
    # Compare the actual value with the user value displayed on the LEDs
    if guess_num == actual_value:
        ## EXACT GUESS
        GPIO.output(tuple([LED_accuracy]) + tuple(LED_value), False)
        print()
        print("Well done CHAMP! You win! {}".format(guess_num))

        name = input('Please enter your name below:\n')[0:3]

        save_scores(name, Num_Guesses)
        
        end_of_game = True
    else:
        accuracy_leds()    
        sleep(0.01)
        # if it's close enough, adjust the buzzer
        if abs(guess_num-actual_value) <= 3:
            trigger_buzzer()

        sleep(1)
        LED_PWM.stop()
        Buzz_PWM.stop()
        Num_Guesses += 1
        #clearLines()
        print("Guess number : {}".format(guess_num))
        


    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    pass


# LED Brightness
def accuracy_leds():
	## DONE
	global guess_num
	global actual_value
	global LED_PWM
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
	if guess_num < actual_value:
		LED_PWM.start((guess_num/actual_value)*100)
	else:
		LED_PWM.start(((8-guess_num)/(8-actual_value))*100)


	pass


# Sound Buzzer
def trigger_buzzer():
    ## FIX SOUND
    global Buzz_PWM
    global guess_num
    global actual_value

    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%

    if abs(guess_num-actual_value) == 3:
        Buzz_PWM.start(50)
        Buzz_PWM.ChangeFrequency(1)	# If the user is off by an absolute value of 3, the buzzer should sound once every second

    elif abs(guess_num-actual_value) == 2:
        Buzz_PWM.start(50)
        Buzz_PWM.ChangeFrequency(2)	# If the user is off by an absolute value of 2, the buzzer should sound twice every second
    elif abs(guess_num-actual_value) == 1:
        Buzz_PWM.start(50)
        Buzz_PWM.ChangeFrequency(4)	# If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    else:
        Buzz_PWM.stop()

    pass

if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()

        eeprom.clear(2048)
        sleep(0.01)
        eeprom.populate_mock_scores()

        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
