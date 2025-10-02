#!/usr/bin/env python3
"""
Geocoding service module
Provides location-to-coordinate conversion using multiple geocoding APIs
"""

import os
import time
import requests
from typing import Dict, Optional, Tuple, List

from .logging_utils import get_logger
from .config import config


class GeocodingService:
    """
    Service for converting locations to coordinates using multiple geocoding providers
    """

    def __init__(self, here_api_key: Optional[str] = None):
        """
        Initialize the geocoding service

        Args:
            here_api_key: HERE API key (if not provided, will use config.HERE_API_KEY)
        """
        self.logger = get_logger()
        self.here_api_key = here_api_key or config.HERE_API_KEY
        self.geocoding_cache = {}

        if self.here_api_key:
            self.logger.info("HERE API key configured for geocoding")
        else:
            self.logger.warning(
                "HERE API key not available - will use Nominatim as fallback"
            )

    def geocode_location(
        self, location: str, use_here_api: bool = True
    ) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location using the best available geocoding service

        Args:
            location: Location string (e.g., "Dallas, TX")
            use_here_api: Whether to prefer HERE API over Nominatim

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if not location or not location.strip():
            return None

        location = location.strip()

        # Check cache first
        if location in self.geocoding_cache:
            return self.geocoding_cache[location]

        # Try HERE API first if available and preferred
        if use_here_api and self.here_api_key:
            coords = self._geocode_here(location)
            if coords:
                return coords

        # Fallback to Nominatim
        coords = self._geocode_nominatim(location)
        return coords

    def _geocode_here(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates using HERE Geocoding API

        Args:
            location: Location string

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            url = "https://geocode.search.hereapi.com/v1/geocode"
            params = {"q": location, "apikey": self.here_api_key, "limit": 1}

            response = requests.get(
                url, params=params, timeout=config.GEOCODING_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            if data.get("items") and len(data["items"]) > 0:
                position = data["items"][0]["position"]
                coords = (position["lat"], position["lng"])

                # Cache the result
                self.geocoding_cache[location] = coords
                self.logger.debug(f"HERE geocoded '{location}' -> {coords}")

                return coords
            else:
                # Cache negative result
                self.geocoding_cache[location] = None
                self.logger.debug(
                    f"HERE geocoding failed for '{location}' - no results"
                )
                return None

        except Exception as e:
            self.logger.warning(f"HERE geocoding failed for '{location}': {e}")
            # Cache failure
            self.geocoding_cache[location] = None
            return None

    def _geocode_nominatim(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates using Nominatim (OpenStreetMap) geocoding

        Args:
            location: Location string

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "countrycodes": "us",  # Limit to US for truck routes
                "addressdetails": 1,
            }

            headers = {"User-Agent": "Driver-Packet-Processor/1.0"}

            # Rate limiting - Nominatim requires respectful usage
            time.sleep(config.NOMINATIM_RATE_LIMIT)

            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                coords = (float(data[0]["lat"]), float(data[0]["lon"]))

                # Cache the result
                self.geocoding_cache[location] = coords
                self.logger.debug(f"Nominatim geocoded '{location}' -> {coords}")

                return coords
            else:
                # Cache negative result
                self.geocoding_cache[location] = None
                self.logger.debug(
                    f"Nominatim geocoding failed for '{location}' - no results"
                )
                return None

        except Exception as e:
            self.logger.warning(f"Nominatim geocoding failed for '{location}': {e}")
            # Cache failure
            self.geocoding_cache[location] = None
            return None

    def get_coordinates_for_stops(
        self, extracted_data: Dict, use_here_api: bool = True
    ) -> Dict:
        """
        Add coordinates for all stops in the extracted data

        Args:
            extracted_data: Dictionary with extracted trip data
            use_here_api: If True, use HERE API; if False, use Nominatim

        Returns:
            Dictionary with coordinate information for each location field
        """
        # Location fields to geocode
        location_fields = [
            "trip_started_from",
            "first_drop",
            "second_drop",
            "third_drop",
            "forth_drop",
            "inbound_pu",
            "drop_off",
        ]

        coordinates = {}

        self.logger.info("Getting coordinates for trip stops...")

        for field in location_fields:
            location = extracted_data.get(field, "")

            # Handle drop_off as array
            if field == "drop_off" and isinstance(location, list):
                if location:
                    # Use the first drop-off location for geocoding
                    location = location[0]
                else:
                    location = ""

            if location and location.strip():
                self.logger.debug(f"Geocoding {field}: {location}")
                coords = self.geocode_location(location, use_here_api)
                if coords:
                    coordinates[field] = {
                        "location": location,
                        "latitude": coords[0],
                        "longitude": coords[1],
                    }
                    self.logger.debug(
                        f"Found coordinates: {coords[0]:.6f}, {coords[1]:.6f}"
                    )
                else:
                    coordinates[field] = {
                        "location": location,
                        "latitude": None,
                        "longitude": None,
                        "geocoding_failed": True,
                    }
                    self.logger.warning(f"Geocoding failed for {field}: {location}")
            else:
                # Empty location field
                coordinates[field] = {
                    "location": "",
                    "latitude": None,
                    "longitude": None,
                }

        # Add summary statistics
        successful_coords = sum(
            1 for coord in coordinates.values() if coord.get("latitude") is not None
        )
        total_locations = sum(
            1 for coord in coordinates.values() if coord.get("location")
        )

        geocoding_summary = {
            "total_locations": total_locations,
            "successful_geocoding": successful_coords,
            "geocoding_success_rate": (
                successful_coords / total_locations if total_locations > 0 else 0
            ),
            "api_used": "HERE" if use_here_api and self.here_api_key else "Nominatim",
        }

        self.logger.info(
            f"Geocoding completed: {successful_coords}/{total_locations} successful "
            f"({geocoding_summary['geocoding_success_rate']:.1%})"
        )

        # Return coordinates with summary
        result = coordinates.copy()
        result["geocoding_summary"] = geocoding_summary

        return result

    def reverse_geocode(self, coords: Tuple[float, float]) -> Optional[str]:
        """
        Reverse geocode coordinates to get location information

        Args:
            coords: (latitude, longitude) tuple

        Returns:
            State abbreviation or None if not found
        """
        if not self.here_api_key:
            return None

        try:
            url = "https://revgeocode.search.hereapi.com/v1/revgeocode"
            params = {
                "at": f"{coords[0]},{coords[1]}",
                "apikey": self.here_api_key,
                "limit": 1,
            }

            response = requests.get(
                url, params=params, timeout=config.GEOCODING_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            if data.get("items") and len(data["items"]) > 0:
                item = data["items"][0]
                address = item.get("address", {})
                state = address.get("state")

                if state:
                    # Convert full state name to abbreviation if needed
                    state_abbrev = self._get_state_abbreviation(state)
                    return state_abbrev

            return None

        except Exception as e:
            self.logger.warning(f"Reverse geocoding failed for {coords}: {e}")
            return None

    def _get_state_abbreviation(self, state_name: str) -> str:
        """Convert state name to abbreviation"""
        state_mapping = {
            "alabama": "AL",
            "alaska": "AK",
            "arizona": "AZ",
            "arkansas": "AR",
            "california": "CA",
            "colorado": "CO",
            "connecticut": "CT",
            "delaware": "DE",
            "florida": "FL",
            "georgia": "GA",
            "hawaii": "HI",
            "idaho": "ID",
            "illinois": "IL",
            "indiana": "IN",
            "iowa": "IA",
            "kansas": "KS",
            "kentucky": "KY",
            "louisiana": "LA",
            "maine": "ME",
            "maryland": "MD",
            "massachusetts": "MA",
            "michigan": "MI",
            "minnesota": "MN",
            "mississippi": "MS",
            "missouri": "MO",
            "montana": "MT",
            "nebraska": "NE",
            "nevada": "NV",
            "new hampshire": "NH",
            "new jersey": "NJ",
            "new mexico": "NM",
            "new york": "NY",
            "north carolina": "NC",
            "north dakota": "ND",
            "ohio": "OH",
            "oklahoma": "OK",
            "oregon": "OR",
            "pennsylvania": "PA",
            "rhode island": "RI",
            "south carolina": "SC",
            "south dakota": "SD",
            "tennessee": "TN",
            "texas": "TX",
            "utah": "UT",
            "vermont": "VT",
            "virginia": "VA",
            "washington": "WA",
            "west virginia": "WV",
            "wisconsin": "WI",
            "wyoming": "WY",
        }

        state_lower = state_name.lower().strip()
        return state_mapping.get(state_lower, state_name.upper()[:2])

    def get_cache_stats(self) -> Dict:
        """
        Get geocoding cache statistics

        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.geocoding_cache)
        successful_entries = sum(
            1 for v in self.geocoding_cache.values() if v is not None
        )
        failed_entries = total_entries - successful_entries

        return {
            "total_cached_locations": total_entries,
            "successful_geocodes": successful_entries,
            "failed_geocodes": failed_entries,
            "success_rate": (
                successful_entries / total_entries if total_entries > 0 else 0
            ),
        }

    def clear_cache(self) -> None:
        """Clear the geocoding cache"""
        self.geocoding_cache.clear()
        self.logger.info("Geocoding cache cleared")
