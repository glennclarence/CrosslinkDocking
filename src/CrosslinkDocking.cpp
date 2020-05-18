#include <pybind11/pybind11.h>
#include <string>
#include <iostream>

namespace py = pybind11;

class CrosslinkDocking
{
public:
    CrosslinkDocking() : _ligand_name("test")
    {
    }
    void add_ligand(std::string pdb_filename)
    {
        std::cout << "the pdb file: " << pdb_filename << " was added " << std::endl;
    }

private:
    std::string _ligand_name;
};

PYBIND11_MODULE(CrosslinkDocking, m)
{
    py::class_<CrosslinkDocking>(m, "CrosslinkDocking")
    .def(py::init())
        .def("add_ligand", &CrosslinkDocking::add_ligand, "Adds a ligand to the system given as the path to a pdb file", py::arg("pdb_filename"))
        .doc() = "Package to perform GPU accelerated Crosslink docking"; // optional module docstring
}
