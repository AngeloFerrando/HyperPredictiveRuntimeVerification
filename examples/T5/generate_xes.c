#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#define INT2VOIDP(i) (void*)(uintptr_t)(i)
#define VOIDP2INT(i) (uintptr_t)(void*)(i)

int c = 0;

void printHeader(){
    printf ("<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n");
    printf ("<log>\n");
    printf ("<string key=\"creator\" value=\"GD\"/>\n");
    printf ("<extension name=\"Concept\" prefix=\"concept\" uri=\"http://code.deckfour.org/xes/concept.xesext\"/>\n");
    printf ("<extension name=\"Time\" prefix=\"time\" uri=\"http://code.deckfour.org/xes/time.xesext\"/>\n");
    printf ("<extension name=\"Organizational\" prefix=\"org\" uri=\"http://code.deckfour.org/xes/org.xesext\"/>\n");
    printf ("<global scope=\"trace\">\n");
    printf ("<string key=\"concept:name\" value=\"name\"/>\n");
    printf ("</global><global scope=\"event\"><string key=\"concept:name\" value=\"name\"/>\n");
    printf ("<date key=\"time:timestamp\" value=\"2011-04-13T14:02:31.199+02:00\"/>\n");
    printf ("<string key=\"Activity\" value=\"string\"/><string key=\"Resource\" value=\"string\"/>\n");
    printf ("</global>\n<classifier name=\"Activity\" keys=\"Activity\"/>\n<classifier name=\"activity classifier\" keys=\"Activity\"/>\n");
    printf ("<trace>\n<string key=\"concept:name\" value=\"3\"/>\n");
    printf ("<string key=\"creator\" value=\"GD\"/>");
}

void printFooter(){
 printf("</log>\n");
}


int main(int argc, char* argv[])
{
    int rt1, rt2;
    pthread_t t1, t2; 
    int N=2;
    if (argc>1) {
      FILE* thread_log;
      thread_log = fopen (argv[1], "r");
      char buf[600];
      char *res;
      printHeader();
      while(1) {
        res=fgets(buf, 600, thread_log );
        if( res==NULL ) break;
        printf("%s",buf);
      }
      printFooter();
		/* chiude i file */
     fclose(thread_log);
    };
    return 0;
}