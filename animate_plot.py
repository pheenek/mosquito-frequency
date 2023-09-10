
import serial
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from datetime import datetime
from threading import Timer

# ser = serial.Serial('/dev/ttyACM0', 57600)
# dim = 0
# xs = []
# for i in range(93, 2000, 31):
#     xs.append(i)

class AnimatedPlot:
    def __init__(self, path, port, s_interval, samples, cycle):
        '''This class creates the matplotlib animated bar graph plot'''
        self.file_path = path
        self.ser_port = port
        self.sample_interval = int(s_interval/0.2)
        self.no_samples = samples
        self.cycle_time = cycle

        # Timer for the interval with which to write data to file
        # self.cycle_timer = Timer(30.0, self.take_readings)
        self.cycle_timer = Timer(1.0, self.take_readings)
        self.record = True
        self.recorded_samples = 0

        style.use('fivethirtyeight')
        self.fig = plt.figure()
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        # 1 by 1 grid plot number 1
        self.ax1 = self.fig.add_subplot(1, 1, 1)
        self.dim = 0
        self.xs = []
        for i in range(93, 2000, 31):
            self.xs.append(i)

        self.ani = animation.FuncAnimation(self.fig, self.animate, repeat_delay=10)
        plt.show()

    def __del__(self):
        '''Cleans up the matplotlib plot'''
        print("Invoking finalizer")
        plt.close(self.fig)

    def take_readings(self):
        ''''''
        # unblocking function
        self.cycle_timer.cancel()
        print("============= UNBLOCK RECORDING ==============")
        self.record = True

    def on_close(self, event):
        '''Executed when exiting the program'''
        print("Closing plot")
        self.__del__()

    def read_serial_data(self):
        '''Reads a single line of raw data from the serial port

        The data read consists of 64 comma-separated values representing 64
        frequency-blocks. The data represents the magnitude (dB) of the detected
        sound frequency for each block
        
        Returns:
            str: a string of raw-data characters terminated by a '\n' character
        '''
        start = False
        ser_str = ""
        while True:
            available = self.ser_port.in_waiting
            if (available > 0):
                # print("available ", available)
                for i in range(available):
                    byte_ch = self.ser_port.read(1)
                    try:
                        ch = byte_ch.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                
                    if (start == False):
                        if (ch == '\n'):
                            start = True
                    else:
                        if (ch == '\n'):
                            # print("String: ", ser_str, " len ", len(ser_str))
                            ser_str += '\n'
                            return ser_str
                        else:
                            ser_str += ch


    def pack_data_to_dict(self):
        '''Stores the raw-data into a dictionary

        The raw data is stored into a dictionary with keys (0-63) corresponding to 64
        frequency blocks
        
        Returns:
            dict: A dictionary containing the data
        '''
        frequencies = {}
        num = ""
        str_data = ""
        try:
            str_data = self.read_serial_data()
        except OSError:
            self.ser_port.close()
            self.__del__()
        print("Serial string: ", str_data)
        count = 0
        for i in range(len(str_data)):
            try:
                if (str_data[i] == ','):
                    frequencies[count] = int(num)
                    count += 1
                    num = ""
                    continue
                elif (str_data[i] == '\n'):
                    frequencies[count] = int(num)
                else:
                    num += str_data[i]
            except ValueError:
                continue

        if (count == 63):
            return frequencies
        else:
            return None


    def write_to_csv(self, data):
        '''Writes the data into the output file'''
        delimiter = ","
        currentDT = datetime.now()
        date_str = currentDT.strftime("%d/%m/%Y")
        time_str = currentDT.strftime("%H:%M:%S")
        data_str = [str(i) for i in data]
        with open(self.file_path, "a") as file_stream:
            file_stream.write(date_str + "," + time_str + ",")
            file_stream.write(delimiter.join(data_str) + "\n")

    def animate(self, i):
        '''Repeatedly called by animation.FuncAnimation to display the animated plot'''
        currentDT = datetime.now()
        time_str = currentDT.strftime("%H:%M:%S:%f")
        print(time_str)
        graph_data = self.pack_data_to_dict()
        print(graph_data)

        if (graph_data != None):
            # Remove the low-frequency noise
            del graph_data[0]
            del graph_data[1]

            # Reload the plot with the newly-acquired data
            ys = list(graph_data.values())
            # print("xs:", len(xs), "ys:", len(ys))

            self.ax1.clear()
            self.ax1.set_ylim(bottom = 0, top = 500, auto = False)
            self.ax1.bar(self.xs, ys, width = 20)

            if (self.record == True):
                if (self.dim == self.sample_interval):
                # if (self.dim == 10):
                    self.dim = 0
                    print("Saving...")
                    self.write_to_csv(ys)
                    self.recorded_samples += 1
                    if (self.recorded_samples == self.no_samples):
                        self.recorded_samples = 0
                        self.record = False
                        # self.cycle_timer = Timer(float(self.cycle_time), self.take_readings)
                        self.cycle_timer = Timer(5.0, self.take_readings)
                        self.cycle_timer.start()

                self.dim+=1

