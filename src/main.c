#include <SDL3/SDL.h>
#include <stdio.h>

int main(int argc, char *argv[])
{
  if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD) != 0)
  {
    printf("SDL init failed: %s\n", SDL_GetError());
    return 1;
  }

  SDL_Log("SDL initialized successfully");

  SDL_Quit();
  return 0;
}
