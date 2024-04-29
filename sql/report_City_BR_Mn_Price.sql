SELECT 
	Address.City, 
	COUNT(Listing.LID) as number, 
	Listing.Bedrooms, 
	AVG(Listing.Price) FROM Listing 

JOIN Address ON Address.LID = Listing.LID 
WHERE Listing.Price > 1000
GROUP BY Address.City, Listing.Bedrooms
ORDER BY Address.City, Listing.Bedrooms DESC

