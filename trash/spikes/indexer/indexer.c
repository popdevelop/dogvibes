#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <string.h>

#define BUF_SIZE (1024*16)

void parse_dir(char *param)
{
  DIR *dir;
  struct dirent *file = NULL;
  int rc = 0;

  if (!(dir = opendir(param))) {
    //printf("No such directory as %s\n", param);
    return;
  }
  while ((file = readdir(dir))) {
    char buffer[BUF_SIZE];
    struct stat sbuf;
    snprintf(buffer, BUF_SIZE, "%s/%s", param, file->d_name);
    if (stat(buffer, &sbuf) == 0) {
      if (S_ISREG(sbuf.st_mode)) {
        // todo: this is where we check if it's an audio file
        if (strstr(file->d_name, ".mp3") != 0) {
          printf("Found file %s\n", file->d_name);
        }
      }
      else if (S_ISDIR(sbuf.st_mode)) {
        if (file->d_name[0] != '.') {
          //printf("Recursing into %s\n", file->d_name);
          parse_dir(buffer);
        }
      }
    } else {
      //printf("Could not stat %s\n", buffer);
    }
  }
 error:
  closedir(dir);
}

int
main(int argc, char *argv[])
{
  parse_dir(argv[1]);

  return 0;
}
