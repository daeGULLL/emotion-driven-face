#include <stdio.h>
#include <signal.h>
#include <wiringPi.h>
#include <wiringPiSPI.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

#define SPI_CHANNEL 0
#define SPI_SPEED   1000000

typedef enum {
    EMO_IDLE,
    EMO_HAPPY,
    EMO_ANGRY,
    EMO_SAD,
    EMO_FEAR,
    EMO_DISGUST,
    EMO_SURPRISE
} Emotion;

typedef enum {
    STATE_IDLE,
    STATE_TRANSITION
} AnimState;

Emotion currentEmotion = EMO_IDLE;
Emotion targetEmotion = EMO_IDLE;

AnimState animState = STATE_IDLE;
int frameIndex = 0;
int transitionStep = 0;

char inputBuf[64];
int inputLen = 0;

void initNonBlockingStdin() {
    int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
}

Emotion parseEmotion(const char* s) {
    if (!strcmp(s, "happy")) return EMO_HAPPY;
    if (!strcmp(s, "angry")) return EMO_ANGRY;
    if (!strcmp(s, "sad")) return EMO_SAD;
    if (!strcmp(s, "fear")) return EMO_FEAR;
    if (!strcmp(s, "disgust")) return EMO_DISGUST;
    if (!strcmp(s, "surprise")) return EMO_SURPRISE;
    return EMO_IDLE;
}

const char* mouth_idle[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". o o o o o o .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_happy1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". o . . . . o .",
    ". . o o o o . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_happy2[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    "o . . . . . . o",
    "o . . . . . . o",
    ". o . . . . o .",
    ". . o o o o . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_happy3[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    "o o o o o o o o",
    "o . . . . . . o",
    ". o . . . . o .",
    ". . o o o o . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_sad1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_angry1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". o o o o o o .",
    "o . o . . o . o",
    "o . o o o o . o",
    ". o . . . . o .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_disgust1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". o o . . . . .",
    "o . . o o o o .",
    ". . . . . . . o",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_disgust2[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". o o o o o o .",
    "o o o o o o o o",
    "o . . . . . . o",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_fear1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    "o . . . . . . o",
    "o o o o o o o o",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_fear2[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    "o . . . . . . o",
    "o . . . . . . o",
    ". o o o o o o .",
    ". . . . . . . .",
};

const char* mouth_sad2[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    "o . . . . . . o",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_surprise1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". . o o o o . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char* mouth_surprise2[8] = {
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    "o . . . . . . o",
    "o . . . . . . o",
    ". o . . . . o .",
    ". . o o o o . .",
    ". . . . . . . .",
};

const char* mouth_talk1[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". . o o o o . .",
    ". . . . . . . .",
};

const char* mouth_talk2[8] = {
    ". . . . . . . .",
    ". . . . . . . .",
    ". . o o o o . .",
    ". o . . . . o .",
    ". o . . . . o .",
    ". . o o o o . .",
    ". . . . . . . .",
    ". . . . . . . .",
};

const char** idleFrames[] = {
    mouth_idle
};

const char** happyFrames[] = {
    mouth_idle,
    mouth_happy1,
    mouth_happy2,
    mouth_happy3
};

const char** sadFrames[] = {
    mouth_idle,
    mouth_happy1,
    mouth_happy2,
};

const char** surpriseFrames[] = {
    mouth_idle,
    mouth_surprise1,
    mouth_talk2,
    mouth_surprise2
};

const char** angryFrames[] = {
    mouth_idle,
    mouth_sad1,
    mouth_angry1,
};

const char** disgustFrames[] = {
    mouth_idle,
    mouth_disgust1,
    mouth_disgust2,
};

const char** fearFrames[] = {
    mouth_idle,
    mouth_surprise1,
    mouth_fear1,
    mouth_fear2
};

const char** talkFrames[] = {
    mouth_idle,
    mouth_talk1,
    mouth_talk2,
    mouth_talk1
};

#define IDLE_FRAME_COUNT 1
#define HAPPY_FRAME_COUNT 4
#define SURPRISE_FRAME_COUNT 4
#define SAD_FRAME_COUNT 3
#define ANGRY_FRAME_COUNT 3
#define FEAR_FRAME_COUNT 4
#define DISGUST_FRAME_COUNT 3
#define TALK_FRAME_COUNT 4

void max7219_send(unsigned char reg, unsigned char data) {
    unsigned char buffer[2] = { reg, data };
    wiringPiSPIDataRW(SPI_CHANNEL, buffer, 2);
}

void max7219_init() {
    max7219_send(0x09, 0x00);
    max7219_send(0x0A, 0x03);
    max7219_send(0x0B, 0x07);
    max7219_send(0x0C, 0x01);
    max7219_send(0x0F, 0x00);
}

void clearMatrix() {
    for (int i = 1; i <= 8; i++) {
        max7219_send(i, 0x00);
    }
}

void handleExit(int sig) {
    printf("\nExiting... Turning off LED matrix.\n");
    clearMatrix();
    exit(0);
}

void display_pattern(const char* pattern[8]) {
    for (int row = 0; row < 8; row++) {
        unsigned char value = 0;
        int idx = 0;

        for (int col = 0; col < 8; col++) {
            char c = pattern[row][idx];
            if (c == 'o' || c == 'O')
                value |= (1 << (7 - col));

            idx += 2;
        }

        max7219_send(row + 1, value);
    }
}

void animateEmotionStep(Emotion emo) {
    switch (emo) {
    case EMO_IDLE:
        display_pattern(idleFrames[0]);
        break;
    case EMO_HAPPY:
        display_pattern(happyFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % HAPPY_FRAME_COUNT;
        break;
    case EMO_SAD:
        display_pattern(sadFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % SAD_FRAME_COUNT;
        break;
    case EMO_ANGRY:
        display_pattern(angryFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % ANGRY_FRAME_COUNT;
        break;
    case EMO_DISGUST:
        display_pattern(disgustFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % DISGUST_FRAME_COUNT;
        break;
    case EMO_FEAR:
        display_pattern(fearFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % FEAR_FRAME_COUNT;
        break;
    case EMO_SURPRISE:
        display_pattern(surpriseFrames[frameIndex]);
        frameIndex = (frameIndex + 1) % SURPRISE_FRAME_COUNT;
        break;
    }
}

int animateTransitionStep(Emotion from, Emotion to) {
    switch (transitionStep) {

    case 0:
        display_pattern(mouth_talk1); 
        break;
    case 1:
        display_pattern(mouth_idle); 
        break;
    case 2:
        frameIndex = 0;               
        return 1;                    
    default:
        return 1; 
    }

    transitionStep++;
    return 0;
}

void onEmotionInput(const char* s) {
    Emotion newEmotion = parseEmotion(s);

    if (newEmotion != targetEmotion) {
        targetEmotion = newEmotion;
        animState = STATE_TRANSITION;
        transitionStep = 0;
        frameIndex = 0;
    }
}

void pollEmotionInput() {
    char ch;
    while (read(STDIN_FILENO, &ch, 1) > 0) {
        if (ch == '\n') {
            inputBuf[inputLen] = 0;
            onEmotionInput(inputBuf);
            inputLen = 0;
        }
        else if (inputLen < sizeof(inputBuf) - 1) {
            inputBuf[inputLen++] = ch;
        }
    }
}

int main() {
    if (wiringPiSetup() == -1)
        return 1;

    wiringPiSPISetup(SPI_CHANNEL, SPI_SPEED);
    max7219_init();
    signal(SIGINT, handleExit);
    initNonBlockingStdin();

    while (1) {
        pollEmotionInput();

        switch (animState) {
        case STATE_IDLE:
            animateEmotionStep(currentEmotion);
            if (currentEmotion != targetEmotion) {
                animState = STATE_TRANSITION;
                transitionStep = 0;
            }
            break;

        case STATE_TRANSITION:
            if (animateTransitionStep(currentEmotion, targetEmotion)) {
                currentEmotion = targetEmotion;
                animState = STATE_IDLE;
            }
            break;
        }

        delay(100);
    }
}

