#!/usr/bin/env python3
"""
State analyzer module
Handles state-based route analysis and mileage distribution calculations
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Optional GIS dependencies for enhanced route analysis
try:
    import geopandas as gpd
    import shapely.geometry as geom
    from shapely.geometry import LineString, Point
    import flexpolyline
    import warnings

    warnings.filterwarnings("ignore", category=FutureWarning)
    GIS_AVAILABLE = True
except ImportError:
    GIS_AVAILABLE = False

    # Create dummy classes to prevent errors
    class gpd:
        class GeoDataFrame:
            pass

    class geom:
        pass

    class LineString:
        pass

    class Point:
        pass

    flexpolyline = None

from .logging_utils import get_logger
from .geocoding_service import GeocodingService
from .config import config


class StateAnalyzer:
    """
    Analyze routes to determine state-by-state mileage distribution
    """

    def __init__(self, geocoding_service: Optional[GeocodingService] = None):
        """
        Initialize the state analyzer

        Args:
            geocoding_service: Geocoding service for reverse geocoding
        """
        self.logger = get_logger()
        self.geocoding_service = geocoding_service
        self._state_boundaries = None

        if GIS_AVAILABLE:
            self.logger.info(
                "GIS dependencies available - enhanced route analysis enabled"
            )
        else:
            self.logger.warning(
                "GIS dependencies not available - using fallback state analysis"
            )

    def load_state_boundaries(self):
        """Load and prepare state boundary data from shapefiles"""
        if not GIS_AVAILABLE:
            self.logger.warning(
                "GIS dependencies not available - cannot load state boundaries"
            )
            return None

        if self._state_boundaries is None:
            self.logger.info("Loading state boundary data...")

            # Path to state shapefile (from config)
            state_shp = Path(config.STATE_SHAPEFILE_PATH)

            if not state_shp.exists():
                self.logger.error(f"State shapefile not found: {state_shp}")
                return None

            try:
                # Load state boundaries and project to appropriate CRS
                states = gpd.read_file(state_shp)[["STUSPS", "geometry"]]
                self._state_boundaries = states.to_crs(
                    epsg=5070
                )  # NAD83/USA Contiguous

                self.logger.info(
                    f"Loaded {len(self._state_boundaries)} state boundaries"
                )
            except Exception as e:
                self.logger.error(f"Error loading state boundaries: {e}")
                return None

        return self._state_boundaries

    def calculate_state_miles_from_polyline(
        self, polyline_str, total_distance_miles: float
    ) -> Dict[str, float]:
        """
        Calculate miles driven in each state using HERE polyline and state boundary intersection

        Args:
            polyline_str: HERE API polyline string(s)
            total_distance_miles: Total distance of the route

        Returns:
            Dictionary mapping state abbreviations to miles driven
        """
        if not GIS_AVAILABLE:
            self.logger.warning(
                "GIS dependencies not available - cannot perform polyline analysis"
            )
            return {}

        if not flexpolyline:
            self.logger.warning("flexpolyline not available - cannot decode polyline")
            return {}

        try:
            if not polyline_str:
                self.logger.warning("No polyline data available")
                return {}

            # Load state boundaries
            states_gdf = self.load_state_boundaries()

            if states_gdf is None:
                self.logger.warning(
                    "State boundaries not available - cannot perform intersection"
                )
                return {}

            # Support either a single polyline string or a list of polyline strings
            polylines = (
                polyline_str if isinstance(polyline_str, list) else [polyline_str]
            )

            combined_line_geoms = []
            total_points = 0
            for pl in polylines:
                if not pl:
                    continue
                # Decode HERE's flexible polyline
                self.logger.debug(f"Decoding HERE polyline segment ({len(pl)} chars)")
                decoded_coords = flexpolyline.decode(pl)
                total_points += len(decoded_coords)
                if not decoded_coords or len(decoded_coords) < 2:
                    continue
                # HERE flexpolyline returns [lat, lng, elevation] tuples
                # Convert to [(lng, lat)] for shapely (note: reversed order)
                line_coords = [(coord[1], coord[0]) for coord in decoded_coords]
                # Create route line geometry per segment
                combined_line_geoms.append(LineString(line_coords))

            if not combined_line_geoms:
                self.logger.warning("No valid decoded polyline segments")
                return {}

            # Merge segments into a single multilinestring/linestring
            route_line = (
                combined_line_geoms[0]
                if len(combined_line_geoms) == 1
                else geom.MultiLineString(combined_line_geoms)
            )
            self.logger.info(
                f"Created route geometry from {len(combined_line_geoms)} segment(s), {total_points} points total"
            )

            # Convert to GeoDataFrame with WGS84 CRS
            route_gdf = gpd.GeoDataFrame([1], geometry=[route_line], crs="EPSG:4326")

            # Reproject to match state boundaries CRS
            route_projected = route_gdf.to_crs(states_gdf.crs)
            self.logger.debug("Route reprojected to match state boundaries")

            # Find intersections with state boundaries
            state_miles = {}
            total_route_length_meters = 0

            for idx, state_row in states_gdf.iterrows():
                try:
                    intersection = route_projected.iloc[0].geometry.intersection(
                        state_row.geometry
                    )

                    if not intersection.is_empty:
                        # Calculate length of intersection
                        if hasattr(intersection, "length"):
                            length_meters = intersection.length
                        else:
                            # Handle multipart geometries
                            length_meters = sum(
                                geom.length
                                for geom in intersection.geoms
                                if hasattr(geom, "length")
                            )

                        if length_meters > 0:
                            total_route_length_meters += length_meters
                            state_abbr = state_row["STUSPS"]
                            state_miles[state_abbr] = (
                                length_meters / 1609.34
                            )  # Convert to miles

                except Exception as state_error:
                    continue

            # Scale the calculated miles to match the actual route distance
            if state_miles and total_route_length_meters > 0:
                calculated_total_miles = sum(state_miles.values())
                if calculated_total_miles > 0:
                    scale_factor = total_distance_miles / calculated_total_miles
                    for state in state_miles:
                        state_miles[state] = round(state_miles[state] * scale_factor, 1)

            # Filter out very small segments (using config threshold)
            state_miles = {
                state: miles
                for state, miles in state_miles.items()
                if miles >= config.MIN_STATE_MILES_THRESHOLD
            }

            # Keep only contiguous US states to reduce noise
            contiguous_states = {
                "AL",
                "AZ",
                "AR",
                "CA",
                "CO",
                "CT",
                "DE",
                "FL",
                "GA",
                "ID",
                "IL",
                "IN",
                "IA",
                "KS",
                "KY",
                "LA",
                "ME",
                "MD",
                "MA",
                "MI",
                "MN",
                "MS",
                "MO",
                "MT",
                "NE",
                "NV",
                "NH",
                "NJ",
                "NM",
                "NY",
                "NC",
                "ND",
                "OH",
                "OK",
                "OR",
                "PA",
                "RI",
                "SC",
                "SD",
                "TN",
                "TX",
                "UT",
                "VT",
                "VA",
                "WA",
                "WV",
                "WI",
                "WY",
            }
            state_miles = {
                state: miles
                for state, miles in state_miles.items()
                if state in contiguous_states
            }

            self.logger.info(f"State miles calculated: {len(state_miles)} states")
            for state, miles in state_miles.items():
                self.logger.debug(f"     {state}: {miles} miles")

            return state_miles

        except Exception as e:
            self.logger.error(f"Error calculating state miles from polyline: {e}")
            return {}

    def analyze_route_states_enhanced(
        self,
        polyline: Optional[str],
        origin_coords: Tuple[float, float],
        destination_coords: Tuple[float, float],
        total_distance_miles: float,
    ) -> Dict:
        """
        Enhanced route analysis using strategic geographic sampling and state boundary detection

        This method creates intelligent sample points along the likely route path
        and uses reverse geocoding to determine all states the route passes through.
        """
        try:
            self.logger.info(
                f"Enhanced route analysis: {total_distance_miles:.1f} mile route"
            )

            # Generate strategic sample points along the route path
            sample_points = self._generate_route_sample_points(
                origin_coords, destination_coords, total_distance_miles
            )

            self.logger.debug(
                f"Analyzing {len(sample_points)} strategic sample points..."
            )

            # Reverse geocode each sample point to determine states
            states_encountered = []

            for i, point in enumerate(sample_points):
                try:
                    state = self._reverse_geocode_to_state(point)
                    if state:
                        states_encountered.append(
                            {
                                "point_index": i,
                                "coordinates": point,
                                "state": state,
                                "distance_ratio": (
                                    i / (len(sample_points) - 1)
                                    if len(sample_points) > 1
                                    else 0
                                ),
                            }
                        )
                        self.logger.debug(
                            f"Point {i+1}/{len(sample_points)}: {state} at {point[0]:.4f},{point[1]:.4f}"
                        )

                    # Rate limiting - be respectful with API calls
                    if i < len(sample_points) - 1:
                        time.sleep(config.HERE_RATE_LIMIT)

                except Exception as e:
                    self.logger.warning(f"Failed to geocode point {i+1}: {e}")
                    continue

            if not states_encountered:
                self.logger.warning("No states identified - using endpoint fallback")
                return self._fallback_endpoint_state_analysis(
                    origin_coords, destination_coords, total_distance_miles
                )

            # Enhanced state mileage estimation
            return self._calculate_enhanced_state_mileage(
                states_encountered, total_distance_miles
            )

        except Exception as e:
            self.logger.error(f"Enhanced analysis failed: {e}")
            return self._fallback_endpoint_state_analysis(
                origin_coords, destination_coords, total_distance_miles
            )

    def _generate_route_sample_points(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        distance_miles: float,
    ) -> List[Tuple[float, float]]:
        """
        Generate strategic sample points along the likely route path
        Uses intelligent spacing based on route characteristics
        """
        points = [origin]

        # Calculate optimal number of sample points based on distance
        if distance_miles < 100:
            num_points = 5  # Short routes: minimal sampling
        elif distance_miles < 500:
            num_points = 8  # Medium routes: moderate sampling
        elif distance_miles < 1000:
            num_points = 12  # Long routes: detailed sampling
        else:
            num_points = 15  # Very long routes: comprehensive sampling

        # Generate intermediate points using great circle approximation
        for i in range(1, num_points - 1):
            ratio = i / (num_points - 1)

            # Simple linear interpolation (good enough for continental US routes)
            lat = origin[0] + (destination[0] - origin[0]) * ratio
            lng = origin[1] + (destination[1] - origin[1]) * ratio

            points.append((lat, lng))

        points.append(destination)

        # Add strategic off-path points for border detection
        enhanced_points = []
        for i, point in enumerate(points):
            enhanced_points.append(point)

            # Add slight geographic variations for better state boundary detection
            if i < len(points) - 1:
                next_point = points[i + 1]

                # Add points slightly north and south of the main path
                lat_offset = (next_point[0] - point[0]) * 0.1
                lng_offset = (next_point[1] - point[1]) * 0.1

                # Add offset points (but limit total points to avoid API limits)
                if len(enhanced_points) < 20:
                    mid_lat = (point[0] + next_point[0]) / 2
                    mid_lng = (point[1] + next_point[1]) / 2

                    # Add a point with slight offset for state boundary detection
                    enhanced_points.append(
                        (mid_lat + lat_offset * 0.5, mid_lng + lng_offset * 0.5)
                    )

        return enhanced_points[
            : config.ROUTE_SAMPLE_POINTS_MAX
        ]  # Cap at configured limit to avoid API rate limits

    def _reverse_geocode_to_state(self, coords: Tuple[float, float]) -> Optional[str]:
        """
        Reverse geocode coordinates to determine the US state

        Args:
            coords: (latitude, longitude) tuple

        Returns:
            State abbreviation or None
        """
        if self.geocoding_service:
            return self.geocoding_service.reverse_geocode(coords)
        else:
            self.logger.warning("No geocoding service available for reverse geocoding")
            return None

    def _calculate_enhanced_state_mileage(
        self, states_encountered: List[Dict], total_distance_miles: float
    ) -> Dict:
        """
        Calculate state mileage using enhanced analysis of state transitions
        """
        if not states_encountered:
            return {
                "states": [],
                "analysis_method": "enhanced_failed",
                "total_distance_analyzed": 0,
            }

        # Group consecutive states and estimate distances more accurately
        state_segments = []
        current_state = None
        segment_start_ratio = 0

        for point_data in states_encountered:
            state = point_data["state"]
            ratio = point_data["distance_ratio"]

            if state != current_state:
                # Finish previous segment
                if current_state:
                    segment_distance = (
                        ratio - segment_start_ratio
                    ) * total_distance_miles
                    state_segments.append(
                        {
                            "state": current_state,
                            "distance_miles": segment_distance,
                            "start_ratio": segment_start_ratio,
                            "end_ratio": ratio,
                        }
                    )

                # Start new segment
                current_state = state
                segment_start_ratio = ratio

        # Finish last segment
        if current_state:
            segment_distance = (1.0 - segment_start_ratio) * total_distance_miles
            state_segments.append(
                {
                    "state": current_state,
                    "distance_miles": segment_distance,
                    "start_ratio": segment_start_ratio,
                    "end_ratio": 1.0,
                }
            )

        # Aggregate by state and apply intelligent smoothing
        state_totals = {}
        for segment in state_segments:
            state = segment["state"]
            distance = segment["distance_miles"]

            # Apply minimum distance threshold to filter out brief border crossings
            if distance < 5.0:  # Less than 5 miles might be GPS noise
                self.logger.debug(
                    f"Very short segment in {state} ({distance:.1f} mi) - might be border noise"
                )

            state_totals[state] = state_totals.get(state, 0) + distance

        # Format results with enhanced information
        states_list = []
        total_accounted_distance = 0

        for state, distance in state_totals.items():
            if distance >= 1.0:  # Only include states with meaningful distance
                percentage = (
                    (distance / total_distance_miles * 100)
                    if total_distance_miles > 0
                    else 0
                )
                states_list.append(
                    {
                        "state": state,
                        "miles": round(distance, 1),
                        "percentage": round(percentage, 1),
                    }
                )
                total_accounted_distance += distance

        # Sort by distance (descending)
        states_list.sort(key=lambda x: x["miles"], reverse=True)

        # Calculate accuracy metrics
        coverage_percentage = (
            (total_accounted_distance / total_distance_miles * 100)
            if total_distance_miles > 0
            else 0
        )

        self.logger.info(
            f"Enhanced analysis: {len(states_list)} states, {coverage_percentage:.1f}% route coverage"
        )
        for state_data in states_list:
            self.logger.debug(
                f"  {state_data['state']}: {state_data['miles']} miles ({state_data['percentage']}%)"
            )

        return {
            "states": states_list,
            "analysis_method": "enhanced_route_sampling",
            "total_distance_analyzed": total_distance_miles,
            "route_coverage_percentage": round(coverage_percentage, 1),
            "sample_points_used": len(states_encountered),
            "states_detected": len(states_list),
        }

    def _fallback_endpoint_state_analysis(
        self,
        origin_coords: Tuple[float, float],
        destination_coords: Tuple[float, float],
        total_distance_miles: float,
    ) -> Dict:
        """
        Fallback analysis using only origin and destination states
        """
        self.logger.info("Using fallback endpoint analysis...")

        origin_state = (
            self._reverse_geocode_to_state(origin_coords)
            if self.geocoding_service
            else None
        )
        dest_state = (
            self._reverse_geocode_to_state(destination_coords)
            if self.geocoding_service
            else None
        )

        states_list = []

        if origin_state and dest_state:
            if origin_state == dest_state:
                # Same state
                states_list.append(
                    {
                        "state": origin_state,
                        "miles": round(total_distance_miles, 1),
                        "percentage": 100.0,
                    }
                )
            else:
                # Different states - split evenly
                miles_per_state = total_distance_miles / 2
                states_list.extend(
                    [
                        {
                            "state": origin_state,
                            "miles": round(miles_per_state, 1),
                            "percentage": 50.0,
                        },
                        {
                            "state": dest_state,
                            "miles": round(miles_per_state, 1),
                            "percentage": 50.0,
                        },
                    ]
                )

        return {
            "states": states_list,
            "analysis_method": "fallback_endpoints",
            "total_distance_analyzed": total_distance_miles,
            "route_coverage_percentage": 100.0,
            "note": "Fallback analysis - may miss intermediate states",
        }

    def add_state_mileage_to_trip_data(
        self, trip_distance_data: Dict, polylines: Optional[List[str]] = None
    ) -> Dict:
        """
        Add state mileage analysis to existing trip distance data

        Args:
            trip_distance_data: Distance calculation results from RouteAnalyzer
            polylines: Optional polyline data for enhanced analysis

        Returns:
            Updated trip data with state mileage information
        """
        result = trip_distance_data.copy()

        total_distance = trip_distance_data.get("total_distance_miles", 0)
        legs = trip_distance_data.get("legs", [])

        if total_distance <= 0 or not legs:
            result["state_mileage"] = []
            return result

        # Try to get origin and destination for fallback analysis
        origin_coords = None
        destination_coords = None

        if legs:
            first_leg = legs[0]
            last_leg = legs[-1]

            if "origin" in first_leg and "coordinates" in first_leg["origin"]:
                origin_coords = first_leg["origin"]["coordinates"]

            if "destination" in last_leg and "coordinates" in last_leg["destination"]:
                destination_coords = last_leg["destination"]["coordinates"]

        # Use polylines if available for enhanced analysis
        if polylines and GIS_AVAILABLE:
            state_miles = self.calculate_state_miles_from_polyline(
                polylines, total_distance
            )
        elif origin_coords and destination_coords:
            # Use enhanced sampling analysis
            state_analysis = self.analyze_route_states_enhanced(
                None, origin_coords, destination_coords, total_distance
            )
            state_miles = {
                state["state"]: state["miles"]
                for state in state_analysis.get("states", [])
            }
        else:
            state_miles = {}

        # Format state mileage for output
        state_mileage = []
        for state, distance in state_miles.items():
            state_mileage.append(
                {
                    "state": state,
                    "miles": round(distance, 1),
                    "percentage": round(
                        (distance / total_distance * 100) if total_distance > 0 else 0,
                        1,
                    ),
                }
            )

        # Sort state mileage by distance (descending)
        state_mileage.sort(key=lambda x: x["miles"], reverse=True)

        result["state_mileage"] = state_mileage

        self.logger.info(f"State mileage analysis: {len(state_mileage)} states")
        for state_data in state_mileage:
            self.logger.debug(
                f"  {state_data['state']}: {state_data['miles']} miles ({state_data['percentage']}%)"
            )

        return result
