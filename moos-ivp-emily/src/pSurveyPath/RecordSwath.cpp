/************************************************************/
/*    NAME: Damian Manda                                    */
/*    ORGN: UNH                                             */
/*    FILE: RecordSwath.cpp                                 */
/*    DATE: 23 Feb 2016                                     */
/************************************************************/

#include "RecordSwath.h"
#include <cmath>
#include <algorithm>
#include "AngleUtils.h"
#include "GeomUtils.h"

//---------------------------------------------------------
// Constructor

RecordSwath::RecordSwath(double interval) : m_min_allowable_swath(0),
                         m_has_records(false), m_acc_dist(0),
                         m_interval(interval), m_output_side(BoatSide::Unknown)
{
  /*
  // Define a precision model using 0,0 as the reference origin
	// and 2.0 as coordinates scale.
	geos::geom::PrecisionModel *pm = new geos::geom::PrecisionModel(
    geos::geom::PrecisionModel::FLOATING);

	// Initialize global factory with defined PrecisionModel
	// and a SRID of -1 (undefined).
	m_geom_factory = geos::geom::GeometryFactory::create(pm, -1);
	// We do not need PrecisionMode object anymore, it has
	// been copied to global_factory private storage
	delete pm;
  */

  m_coverage = m_geom_factory->createPolygon();

  // Initialize the point records
  m_interval_swath[BoatSide::Port] = std::vector<double>();
  m_interval_swath[BoatSide::Stbd] = std::vector<double>();
  m_outer_points[BoatSide::Port] = std::vector<geos::geom::Point*>();
  m_outer_points[BoatSide::Stbd] = std::vector<geos::geom::Point*>();
}

bool RecordSwath::AddRecord(double swath_stbd, double swath_port, double loc_x,
                            double loc_y, double heading) {
  SwathRecord record = {loc_x, loc_y, heading, swath_stbd, swath_port};
  m_interval_record.push_back(record);
  m_interval_swath[BoatSide::Stbd].push_back(swath_stbd);
  m_interval_swath[BoatSide::Port].push_back(swath_port);

  if (m_has_records) {
    m_acc_dist += distPointToPoint(m_last_x, m_last_y, loc_x, loc_y);
    if (m_acc_dist > m_interval) {
      m_acc_dist = 0;
      MinInterval();
    }
  }

  // Add progressively to the coverage model
  return AddToCoverage(record);

  m_has_records = true;
}

bool RecordSwath::AddToCoverage(SwathRecord record) {
  // Tackle this later
  return true;
}

void RecordSwath::MinInterval() {
  // Get the record from the side we are offsetting
  std::vector<double>* side_record = &m_interval_swath[m_output_side];

  int min_index = 0;
  if (side_record->size() > 0) {
    min_index = std::min_element(side_record->begin(), side_record->end())
      - side_record->begin();
  }

  if (m_interval_record.size() > min_index) {
    // Add the first point if this is the first interval in the record
    if (m_min_record.size() == 0 && min_index != 0) {
      m_min_record.push_back(m_interval_record[0]);
    }
    m_min_record.push_back(m_interval_record[min_index]);
    // These are always cleared in the python version
    m_interval_record.clear();
    m_interval_swath.clear();
  }
}

bool RecordSwath::SaveLast() {
  if (m_min_record.size() > 0) {
    SwathRecord last_min = m_min_record.back();
    SwathRecord last_rec = m_interval_record.back();
    if (last_min.loc_x != last_rec.loc_x && last_min.loc_y != last_rec.loc_y) {
      m_min_record.push_back(last_rec);
    }
    return true;
  }
  return false;
}

void RecordSwath::ResetLine() {
  m_interval_record.clear();
  m_interval_swath[BoatSide::Stbd].clear();
  m_interval_swath[BoatSide::Port].clear();
  m_coverage = m_geom_factory->createPolygon();
  m_outer_points[BoatSide::Stbd].clear();
  m_outer_points[BoatSide::Port].clear();
  m_acc_dist = 0;
  m_has_records = false;
}

XYSegList RecordSwath::GetSwathOuterPts(BoatSide side) {
  XYSegList points;
  std::list<SwathRecord>::iterator record;
  for (record = m_min_record.begin(); record != m_min_record.end(); record++) {
    XYPoint outer_pt = GetOuterPoint(*record, m_output_side);
    points.add_vertex(outer_pt);
  }
  return points;
}

XYPoint RecordSwath::GetOuterPoint(const SwathRecord &record, BoatSide side) {
  // Could have SwathRecord be a class with functions to return representation
  // as a vector or point.
  double swath_width = 0;
  double rotate_degs = 0;
  if (side == BoatSide::Stbd) {
    swath_width = record.swath_stbd;
    rotate_degs = 90;
  } else if (side == BoatSide::Port) {
    swath_width = record.swath_port;
    rotate_degs = -90;
  }
  XYVector swath_vector(record.loc_x, record.loc_y, swath_width,
    record.heading);
  swath_vector.augAngle(rotate_degs);
  return XYPoint(swath_vector.xpos() + swath_vector.xdot(),
    swath_vector.ypos() + swath_vector.ydot());
}

double RecordSwath::GetSwathWidth(BoatSide side, unsigned int index) {
  if (side == BoatSide::Stbd) {
    return m_min_record[index].swath_stbd;
  } else if (side == BoatSide::Stbd) {
    return m_min_record[index].swath_port;
  }
}
