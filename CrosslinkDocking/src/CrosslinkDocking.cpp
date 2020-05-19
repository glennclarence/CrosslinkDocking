#include <pybind11/pybind11.h>
#include <string>
#include <iostream>
#include "Server.h"
#include "DataManager.h"
#include "Service.h"
#include "ServiceFactory.h"
#include <memory>
#include "RequestHandler.h"
#include "Types_6D.h"
#include "Request.h"
#include "readFile.h"
#include "Chunk.h"

namespace py = pybind11;

class CrosslinkDocking
{
public:
    CrosslinkDocking() : _ligand_name("test")
    {
        std::vector<int> device_ids;
        device_ids.push_back(0);

        std::shared_ptr<as::Service<as::Types_6D<float>>> service = std::move(std::static_pointer_cast<as::Service<as::Types_6D<float>>>(as::ServiceFactory::create<float>(as::ServiceType::CPUEnergyService6D, _data_manager,device_ids)));
        auto server = std::shared_ptr<as::Server<as::Types_6D<float>>>(new as::Server<as::Types_6D<float>>(service));
        std::vector<as::DOF_6D<float>> dofs;
        as::Common common;
	    as::RequestHandler<as::Types_6D<float>> requestHandler = as::RequestHandler<as::Types_6D<float>>::newBuilder()
	 		.withServer(server)
	 		.withCommon(common)
	 		.withDofs(_dofs)
	 		.withSolverName("VA13")
	 		.build();
    }

    int add_ligand(std::string pdb_filename)
    {

       // auto ligand = as::createProteinFromPDB<float>(pdb_filename);
        std::cout << "the pdb file: " << pdb_filename << " was added " << std::endl;
        //_data_manager->add(ligand);
    }

    void add_starting_positions(std::string dof_filename)
    {

        std::cout << "the dof file: " << dof_filename << " was added " << std::endl;

    }

private:
    std::string _ligand_name;
    std::shared_ptr<as::DataManager> _data_manager;
    std::vector<as::DOF_6D<float>> _dofs;
};

PYBIND11_MODULE(CrosslinkDocking, m)
{
    py::class_<CrosslinkDocking>(m, "CrosslinkDocking")
    .def(py::init())
        .def("add_ligand", &CrosslinkDocking::add_ligand, "Adds a ligand to the system given as the path to a pdb file", py::arg("pdb_filename"))
        .def("add_starting_positions", &CrosslinkDocking::add_starting_positions, "Adds a starting positions to the system given as the path to a degree of freedom file", py::arg("dof_filename"))
        .doc() = "Package to perform GPU accelerated Crosslink docking"; // optional module docstring
} 
