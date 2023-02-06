#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#define INT2VOIDP(i) (void*)(uintptr_t)(i)
#define VOIDP2INT(i) (uintptr_t)(void*)(i)


int c = 0;

void printEvent(FILE* thread_log,char* THREAD,char * EVENT){
  fprintf (thread_log,"<event>\n<string key=\"concept:name\" value=\"%s\"/>\n<date key=\"time:timestamp\" value=\"2021-12-30T14:34:00.000+01:00\"/>\n<string key=\"Activity\" value=\"%s\"/>\n<string key=\"Resource\" value=\"%s\"/>\n</event>\n",EVENT,EVENT,THREAD);
}

void* fnC1(void* a)
{ int tmp;
  int k = VOIDP2INT(a);

  char thread_log_filename[20];
  FILE* thread_log;
  thread_log = fopen ("log2p", "a");
  fprintf (thread_log,"<trace>\n<string key=\"concept:name\" value=\"3\"/>\n");
  fprintf (thread_log,"<string key=\"creator\" value=\"GD\"/>\n");
  char event[30];

  printEvent(thread_log,"Thread1","create_lock(l1-1)");
  for(int i=0;i<k;i++) {
      //c=c+10
      printEvent(thread_log,"Thread1","lock(l1)");
      sprintf(event, "read_shared_data(c%d)",i);
      printEvent(thread_log,"Thread1",event);
      sprintf(event, "write_shared_data(c%d)",i);
      printEvent(thread_log,"Thread1",event);
      printEvent(thread_log,"Thread1","unlock(l1)");
      sprintf(event, "stop%d",i);
      printEvent(thread_log,"Thread1",event);
    }

  fprintf (thread_log, "%s\n", "</trace>\n");
  fclose(thread_log);
  return(0);
}

int main(int argc, char* argv[])
{
    int rt1, rt2;
    pthread_t t1, t2;
    int N=2;
    if (argc>1) N=atoi(argv[1]);
    void *val = INT2VOIDP(N);

    rt1=pthread_create(&t1, NULL, fnC1, val);
    pthread_join(t1, NULL);

    return 0;
}
