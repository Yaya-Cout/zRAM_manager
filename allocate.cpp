// Script to allocate memory for nothing, just to test the swap manager.
#include <stdiço.h>
#include <stdlib.h>
#include <cstdlib>
#include <unistd.h>
#include <cstring>

long int waittime = 30*1000; // In seconds
long int memory = 500; // In Go
long int splitBy = 500; // In Mo

int main () {
   printf("Allocating %li Go\n", memory);
   memory = memory*1000*1000*1000;
   splitBy = splitBy*1000*1000;
   long int allowBy = memory/splitBy;
   for (int i = 0; i < splitBy; ++i) {
       malloc(allowBy);
   }

   printf("Allocated %li Go\n", memory);

   printf("Exiting\n");

   return(0);
}
