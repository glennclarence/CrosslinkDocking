/*
 * ServiceFactory.h
 *
 *  Created on: Aug 12, 2017
 *      Author: uwe
 */

#ifndef SRC_SERVICE_SERVICEFACTORY_H_
#define SRC_SERVICE_SERVICEFACTORY_H_

#include <memory>
#include "ServiceType.h"
#include "GenericTypes.h"
#include <vector>

namespace as {

template<typename GenericTypes>
class Service;

class CmdArgs;
class DataManager;

class ServiceFactory {
public:
	ServiceFactory() = delete;

//	template<typename REAL, template <typename REAL> class GenericTypes>
//	static std::unique_ptr<Service<GenericTypes<REAL>>> create(ServiceType, std::shared_ptr<DataManager>, CmdArgs const&);

	template<typename REAL>
	static std::shared_ptr<void> create(ServiceType, std::shared_ptr<DataManager>, CmdArgs const&);
	template<typename REAL>
	static std::shared_ptr<void> create(ServiceType, std::shared_ptr<DataManager>, std::vector<int> const & device_ids);

};

}  // namespace as

#endif /* SRC_SERVICE_SERVICEFACTORY_H_ */
