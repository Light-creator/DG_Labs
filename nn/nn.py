import os

train_people_dir = os.path.join("train/people")
train_monkey_dir = os.path.join("train/monkey")
valid_people_dir = os.path.join("valid/people")
valid_monkey_dir = os.path.join("valid/monkey")

print("People training count: ", len(os.listdir(train_people_dir)))
print("Monkey training count: ", len(os.listdir(train_monkey_dir)))
print("People validation count: ", len(os.listdir(valid_people_dir)))
print("Monkey validation count: ", len(os.listdir(valid_monkey_dir)))

from tensorflow.keras.preprocessing.image import ImageDataGenerator

train_datagen = ImageDataGenerator(rescale=1/255)
valid_datagen = ImageDataGenerator(rescale=1/255)

train_gen = train_datagen.flow_from_directory(
        '/tmp/train/',
        classes = ['people', 'monkey'],
        target_size=(200, 200)
        )
