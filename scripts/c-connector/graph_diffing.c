#include <Python.h>

int diff_graph(char* filename1, char* filename2) {
  Py_SetProgramName("Graph_Diffing");  /* optional but recommended */
  Py_Initialize();
  char buf[500];
  strcpy(buf, "import memorydump as md\n"
	 "import graph_generator as gg\n"
	 "import graph_diffing as gd\n"
	 "dump1 = md.load_memory_dump('");
  strcat(buf, filename1);
  strcat(buf, "')\n");
  strcat(buf, "dump2 = md.load_memory_dump('");
  strcat(buf, filename2);
  strcat(buf, "')\n");
  strcat(buf, "graph1 = gg.generate_graph(dump1)\n"
	 "graph2 = gg.generate_graph(dump2)\n"
	 "diff = gd.diff_memory_graphs([graph1, graph2])\n"
	 "gd.extract_diff_graph(graph2, diff)\n");
  PyRun_SimpleString(buf);
  Py_Finalize();
  return 0;
}

