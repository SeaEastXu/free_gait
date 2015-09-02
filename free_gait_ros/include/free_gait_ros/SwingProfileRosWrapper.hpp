/*
 * SwingProfileRosWrapper.hpp
 *
 *  Created on: Mar 6, 2015
 *      Author: Péter Fankhauser
 *   Institute: ETH Zurich, Autonomous Systems Lab
 */

#pragma once

// Free Gait
#include "free_gait_core/free_gait_core.hpp"

// ROS
#include <free_gait_msgs/SwingProfile.h>

// STD
#include <string>

namespace free_gait {

class SwingProfileRosWrapper : public SwingProfile
{
 public:
  SwingProfileRosWrapper();
  virtual ~SwingProfileRosWrapper();

  /*!
   * Populate swing profile from ROS swing profile message.
   * @param message the swing profile ROS message.
   */
  bool fromMessage(const free_gait_msgs::SwingProfile& message);
};

} /* namespace */
