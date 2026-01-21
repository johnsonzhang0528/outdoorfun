export const isValidSpot = (spot) => {
  return (
    spot.description && 
    spot.description.length > 20 && 
    spot.lat && 
    spot.lng
  );
};

export const getValidSpots = (rawSpots) => {
  return rawSpots.filter(isValidSpot);
};
