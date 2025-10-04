#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:5000/api/process_message/"

echo "Seeding resource messages into $BASE_URL ..."

# 1. Explicit location near Eiffel Tower
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "We have 10 large generators and 50 blankets available for distribution.",
  "metadata": {
    "phone_number": "+33612345678",
    "location": {
      "type": "Point",
      "coordinates": [2.2945, 48.8584],
      "properties": {"display_name": "Eiffel Tower, Paris"}
    },
    "user_type": "corporate"
  }
}'
echo -e "\n[1] Done."

# 2. Near Eiffel Tower (implicit)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "I can offer 200 bottles of water and a few first aid kits near the Eiffel Tower.",
  "metadata": {
    "phone_number": "+33698765432",
    "user_type": "civilian"
  }
}'
echo -e "\n[2] Done."

# 3. Paris street (Rue de Rivoli)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "We have extra tents, sleeping bags, and 30 packs of food stored on Rue de Rivoli in Paris.",
  "metadata": {
    "phone_number": "+33123456789",
    "user_type": "NGO"
  }
}'
echo -e "\n[3] Done."

# 4. Park Carol I - Bucharest (implicit)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "Near Park Carol I in Bucharest, we have a stock of medical supplies, tents, and 5 generators.",
  "metadata": {
    "phone_number": "+40721234567",
    "user_type": "corporate entity"
  }
}'
echo -e "\n[4] Done."

# 5. Explicit Bucharest location (Strada General Candiano Popescu)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "We can provide 100 liters of clean water and 20 portable heaters.",
  "metadata": {
    "phone_number": "+40726543210",
    "location": {
      "type": "Point",
      "coordinates": [26.096306, 44.427327],
      "properties": {"display_name": "Strada General Candiano Popescu, near Park Carol I, Bucharest"}
    },
    "user_type": "civilian"
  }
}'
echo -e "\n[5] Done."

# 6. Helsinki Central Station (implicit)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "At the Helsinki Central Station we have 4 rescue boats, 2 pallets of bottled water, and several first aid kits ready.",
  "metadata": {
    "phone_number": "+358401234567",
    "user_type": "NGO"
  }
}'
echo -e "\n[6] Done."

# 7. K-Market Kilpisjärvi (implicit)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "I have a few power generators and 3 dozen water bottles available near K-Market Kilpisjärvi.",
  "metadata": {
    "phone_number": "+358409876543",
    "user_type": "civilian"
  }
}'
echo -e "\n[7] Done."

# 8. Arc de Triomphe (vague quantities)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "We can offer some medical kits, a couple of portable generators, and food supplies close to the Arc de Triomphe.",
  "metadata": {
    "phone_number": "+33699988877",
    "user_type": "corporate"
  }
}'
echo -e "\n[8] Done."

# 9. Louvre Museum (explicit location, no location in text)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "We have 500 liters of water and 10 tents.",
  "metadata": {
    "phone_number": "+33611122233",
    "location": {
      "type": "Point",
      "coordinates": [2.3333, 48.8667],
      "properties": {"display_name": "Louvre Museum, Paris"}
    },
    "user_type": "NGO"
  }
}'
echo -e "\n[9] Done."

# 10. Palace of Parliament, Bucharest (implicit landmark)
curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d '{
  "text": "Near the Palace of Parliament in Bucharest, we have some construction equipment, medical tents, and power tools available.",
  "metadata": {
    "phone_number": "+40731112233",
    "user_type": "corporate entity"
  }
}'
echo -e "\n[10] Done."

echo "✅ Seeding complete."
