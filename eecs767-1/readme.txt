Updated 2/14/2014

I've put in a basic Tornado webserver framework in place.  Using this framework, we can have a simple form that upon submission can call off to a query function that will be able to do the calculations of the query using the dictionary data that will be produced in the preprocess.py and additional code to be written.

I've also checked in the Jquery ui package, which is a very lightweight framework we can use at some point to decorate the page and create a nicer looking interface.  Doing so will require some additional work to implement Ajax requests and to get javascript working in general.  I'm currently looking into the easiest way to do that, but for now we have a good starting point.

As an additional note, the indexer/processor can be run in a separte IOLOOP as part of the server process, so it can kick off and update at different intervals, a very nice feature moving forward.


