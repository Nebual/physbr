#include "Python.h"

//http://superjared.com/entry/anatomy-python-c-module/
/*
i takes 3 TU
iiii takes 5 TU
dddd takes 7 TU
(dd)(dd) takes 10.5 TU
*/

static PyObject * calculatedistance(PyObject *self, PyObject *args) { // THIS TAKES 5 TIMES, and one i takes 3.5 times.
	double x1,x2,y1,y2;
	//int x1,x2,y1,y2;

	if (!PyArg_ParseTuple(args, "(dd)(dd)", &x1,&y1,&x2,&y2))
	//if (!PyArg_ParseTuple(args, "iiii",&x1,&y1,&x2,&y2))
        	return NULL;
	//sts = system(command);
	return Py_BuildValue("d", sqrt(((x1 - x2) * (x1 - x2)) + ((y1 - y2) * (y1 - y2))));
}
static PyMethodDef SpamMethods[] = {
	{"getdistance",  calculatedistance, METH_VARARGS, "Determines the distance between two points."},
	//{"getdistance2",  calculatedistance2, METH_VARARGS, "Determines the distance between two points."},
	//{"getdistance3",  calculatedistance3, METH_VARARGS, "Determines the distance between two points."},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initphysbr(void) {
	(void) Py_InitModule("physbr", SpamMethods);
}
