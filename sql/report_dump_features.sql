SELECT 
  A.LID,
  A.StreetAddress, 
  A.City,
  A.PCode,
  A.HType,
  L.Bedrooms,
  L.Bathrooms,
  L.Sqft,
  L.AgreeType,
  L.Price,
  U.Hydro,
  U.Water,
  U.Heat,
  O.DateString
FROM
	Address AS A
JOIN Listing AS L
	ON A.LID = L.LID
JOIN Utilities AS U
	ON A.LID = U.LID
JOIN Udate AS O
	ON A.LID = O.LID

