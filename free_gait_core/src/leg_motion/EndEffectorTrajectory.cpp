/*
 * EndEffectorTrajectory.hpp
 *
 *  Created on: Mar 16, 2016
 *      Author: Péter Fankhauser
 *   Institute: ETH Zurich, Autonomous Systems Lab
 */

#include <free_gait_core/leg_motion/EndEffectorTrajectory.hpp>
#include <free_gait_core/leg_motion/LegMotionBase.hpp>

// Robot utils
#include <robot_utils/function_approximators/polynomialSplines/PolynomialSplineContainer.hpp>

// Roco
#include <roco/log/log_messages.hpp>

namespace free_gait {

EndEffectorTrajectory::EndEffectorTrajectory(LimbEnum limb)
    : EndEffectorMotionBase(LegMotionBase::Type::EndEffectorTrajectory, limb),
      duration_(0.0),
      ignoreContact_(false),
      ignoreForPoseAdaptation_(false),
      isComputed_(false)
{
}

EndEffectorTrajectory::~EndEffectorTrajectory()
{
}

std::unique_ptr<LegMotionBase> EndEffectorTrajectory::clone() const
{
  std::unique_ptr<LegMotionBase> pointer(new EndEffectorTrajectory(*this));
  return pointer;
}

const ControlSetup EndEffectorTrajectory::getControlSetup() const
{
  return controlSetup_;
}

void EndEffectorTrajectory::updateStartPosition(const Position& startPosition)
{
  isComputed_ = false;
  auto& values = values_.at(ControlLevel::Position);
  if (times_[0] == 0.0) {
    values[0] = startPosition.vector();
  } else {
    times_.insert(times_.begin(), 0.0);
    values.insert(values.begin(), startPosition.vector());
  }
}

bool EndEffectorTrajectory::prepareComputation(const State& state, const Step& step, const AdapterBase& adapter)
{
  duration_ = times_.back();
  trajectory_.fitCurve(times_, values_.at(ControlLevel::Position));
  isComputed_ = true;
  return true;
}

bool EndEffectorTrajectory::needsComputation() const
{
  return false;
}

bool EndEffectorTrajectory::isComputed() const
{
  return isComputed_;
}

const Position EndEffectorTrajectory::evaluatePosition(const double time) const
{
  Position position;
  trajectory_.evaluate(position.toImplementation(), time);
  return position;
}

double EndEffectorTrajectory::getDuration() const
{
  return trajectory_.getMaxTime() - trajectory_.getMinTime();
}

const Position EndEffectorTrajectory::getTargetPosition() const
{
  return Position(values_.at(ControlLevel::Position).back());
}

const std::string& EndEffectorTrajectory::getFrameId(const ControlLevel& controlLevel) const
{
  return frameIds_.at(controlLevel);
}

bool EndEffectorTrajectory::isIgnoreContact() const
{
  return ignoreContact_;
}

bool EndEffectorTrajectory::isIgnoreForPoseAdaptation() const
{
  return ignoreForPoseAdaptation_;
}

std::ostream& operator<<(std::ostream& out, const EndEffectorTrajectory& endEffectorTrajectory)
{
  out << "Duration: " << endEffectorTrajectory.getDuration() << std::endl;
  out << "Ignore contact: " << (endEffectorTrajectory.isIgnoreContact() ? "True" : "False") << std::endl;
  out << "Ignore for pose adaptation: " << (endEffectorTrajectory.isIgnoreForPoseAdaptation() ? "True" : "False") << std::endl;
  out << "Times: ";
  for (const auto& time : endEffectorTrajectory.times_) out << time << ", ";
  out << std::endl;
  out << "Positions: ";
  for (const auto& position : endEffectorTrajectory.values_.at(ControlLevel::Position)) out << "[" << position.transpose() << "], ";
  out << std::endl;
  return out;
}

} /* namespace */
