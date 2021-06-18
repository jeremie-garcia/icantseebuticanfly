#include <Arduino.h>

// WRIST + VIBRATOR ID
const int WRST1_VIBE1 = 3;
const int WRST1_VIBE2 = 5;
const int WRST1_VIBE3 = 6;
const int WRST1_VIBE4 = 9;
const int WRST2_VIBE1 = 10;
const int WRST2_VIBE2 = 11;

const char START_CMD_CHAR = '<';
const char END_CMD_CHAR = '>';



const byte MESSAGE_SIZE = 32;
char message[MESSAGE_SIZE];

String data = "data 0.0 0.0 0.0 0.0 0.0";
boolean newData = false;
int vibrators[6];

void setup() {
    // Initialisation if outpin and
    // make sure there is no power going through
    Serial.begin(115200);
    Serial.println("<Arduino is ready>");
    vibrators[0] = WRST1_VIBE1;
    vibrators[1] = WRST1_VIBE2;
    vibrators[2] = WRST1_VIBE3;
    vibrators[3] = WRST1_VIBE4;
    vibrators[4] = WRST2_VIBE1;
    vibrators[5] = WRST2_VIBE2;
    pinMode(WRST1_VIBE1,OUTPUT);
    pinMode(WRST1_VIBE2,OUTPUT);
    pinMode(WRST1_VIBE3,OUTPUT);
    pinMode(WRST1_VIBE4,OUTPUT);
    pinMode(WRST2_VIBE1,OUTPUT);
    pinMode(WRST2_VIBE2,OUTPUT);
    analogWrite(WRST1_VIBE1,0);
    analogWrite(WRST1_VIBE2,0);
    analogWrite(WRST1_VIBE3,0);
    analogWrite(WRST1_VIBE4,0);
    analogWrite(WRST2_VIBE1,0);
    analogWrite(WRST2_VIBE2,0);
}

void receiveMessage(){
  static boolean receiving = false;
  static byte ndx = 0;
  char rc;

  while (Serial.available() > 0 && newData == false) {
    // We are still receiving data from current message
    // Read the incoming character
    rc = Serial.read();
    if (receiving) {
      //if the charater is not the end of a message
      if (rc != END_CMD_CHAR) {
        //then we store the character to process when the message is complete
        message[ndx++] = rc;
        // The message should not be bigger than 32 characters maximum
        if (ndx >= MESSAGE_SIZE) {
          ndx = MESSAGE_SIZE - 1;
        }
      }
      //The message is whole and we need to process it
      else {
        message[ndx] = '\0'; // terminate the string
        receiving = false;
        ndx = 0;
        newData = true;
      }
    }
    // Waiting for receiving the start command character
    else if (rc == START_CMD_CHAR) receiving = true;
  }
}


void processMessage(){
  //Remove white spaces at the beginning of the message
  data = String(message);
  data.trim();
  int amplitudes[6];
  int idx = 0;
  //Serial.println(data);
  //We need to make sure that the command is valid
  if (newData){
    if (data.startsWith("data ")) {
      //If so we remove the useless part of the command
      data = ' ' + data.substring(5, data.length());
      //Serial.println(data);
      //Parse the command to get the amplitude values
      for (int i=0; (i < data.length()) & (idx < 6); i++){
        if (data[i] == ' '){
          char value[3];
          for (int j=0; j<3; j++) {
              value[j] = data[i+1+j];
          }
          //Serial.println(value);
          String valString = String(value);
          // We use 150 as max so the voltage should go beyond 2V and 3V
          // So theoritically the values that should be sent
          //to the arduino are between 0.7 and 1.0
          amplitudes[idx++] = int(valString.toFloat() * 153);
          //i = i + 3;
        }
      }
      //Then we trigger the vibrators
      for (int i = 0; i < 6; i++) {
        analogWrite(vibrators[i], amplitudes[i]);
        //Serial.print("Vibrating vibrator ");
        //Serial.print(i+1);
        //Serial.print(" to ");
        //Serial.println(amplitudes[i]);
      }
    }
    //command for quick test to check
    //if all the vibrators are working fine
    //command to send is <test>
    if (data.startsWith("test")) {
        int amplitude = 102;
        //Run some test to check all the vibrators
        for (int i = 0; i < 6; i++) {
          analogWrite(vibrators[i], amplitude);
          delay(1000);
          analogWrite(vibrators[i], 0);
        }
    }
    Serial.println("Command processed.");
    newData = false;
  }
}

void loop() {
  //Listen for new command messages
  receiveMessage();
  //Process message and trigger actuators
  processMessage();
}
