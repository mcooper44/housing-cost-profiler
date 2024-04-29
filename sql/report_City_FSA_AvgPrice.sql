SELECT 
	Address.City, 
	substr(Address.PCode, 1,3) as FSA, 
	avg(Listing.Price) as AvgPrice, 
	count(Address.City) as Number
FROM 
	Address
JOIN 
	Listing ON Listing.LID = Address.LID
WHERE 
	Listing.Price > 1000
GROUP BY 
	FSA
ORDER BY Address.City, AvgPrice DESC