export PROJECT_DIR="/home/samir/workspace/dbt-learning"

RAW_DATA="$PROJECT_DIR/temp/raw-data"

echo ""
echo "Downloading data..."

if [ ! -d "$RAW_DATA" ]; then
    echo "" 
    echo "Creating path: $RAW_DATA"
    mkdir -p "$RAW_DATA"
fi

echo ""
if [ -f "$RAW_DATA/addresses.csv" ]; then
    echo "addresses.csv already exist in: $RAW_DATA"
else
    echo "Downloading addresses.csv"
    if curl "https://raw.githubusercontent.com/davidasboth/solve-any-data-analysis-problem/a2612923f23c15dcefbb482a5806861faed0ae51/chapter-2/data/addresses.csv" \
    -o "$RAW_DATA/addresses.csv"; then
        echo "File downloaded in: $RAW_DATA"
    else
        echo "Error downloading the file"
        exit 1
    fi
fi

echo ""
if [ -f "$RAW_DATA/cities.csv" ]; then
    echo "cities.csv already exist in: $RAW_DATA"
else
    echo "Downloading cities.csv"
    if curl "https://raw.githubusercontent.com/davidasboth/solve-any-data-analysis-problem/a2612923f23c15dcefbb482a5806861faed0ae51/chapter-2/data/cities.csv" \
    -o "$RAW_DATA/cities.csv"; then
        echo "File downloaded in: $RAW_DATA"
    else
        echo "Error downloading the file"
        exit 1
    fi
fi

echo ""
echo "### Data Downloaded ###"


echo ""
echo "Connecting to database..." 

PGPASSWORD="analytics" psql -h localhost -d analytics -U analytics -v ON_ERROR_STOP=1 \
    -c "create schema if not exists dbt" \
    -c "create table if not exists dbt.addresses (company_id text, address text, total_spend text)" \
    -c "\copy dbt.addresses (company_id, address, total_spend) from '$RAW_DATA/addresses.csv' delimiters ',' CSV header quote as '\"'" \
    -c "create table if not exists dbt.cities (city text);" \
     -c "\copy dbt.cities (city) from '$RAW_DATA/cities.csv' delimiters ',' CSV"    
 
echo ""
echo "### Successfully imported data into the database ###"

echo ""