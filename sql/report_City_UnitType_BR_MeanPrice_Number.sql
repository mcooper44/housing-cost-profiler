SELECT Address.City as City, Address.HType as Type, Listing.Bedrooms as Bedrms, AVG(Listing.Price) as AvgPrice , COUNT(Listing.Bedrooms) as SampleSize
FROM Address
JOIN Listing on Listing.LID = Address.LID
WHERE Listing.Price > 1000
GROUP BY
Address.City, Address.HType, Listing.Bedrooms
ORDER BY
Address.City, Address.HType, Listing.Bedrooms DESC