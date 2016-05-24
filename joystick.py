import pygame
print("OK")
pygame.init()
pygame.display.set_mode((640,480))

while True:
    for event in pygame.event.get():
        print(event)
