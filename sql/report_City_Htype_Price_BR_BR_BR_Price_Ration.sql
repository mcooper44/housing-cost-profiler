SELECT Address.LID, Address.City, Address.PCode, Address.HType, 
	Listing.Price, Listing.Bedrooms, Listing.Bathrooms, Listing.Price / Listing.Bedrooms
FROM Address
JOIN Listing ON Listing.LID = Address.LID
WHERE Address.City = "Cambridge" AND Listing.Price > 1000 AND Listing.Bedrooms > 0
