!pip install rdflib
!pip install urllib
!pip install pyvis openpyxl

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd
from urllib.parse import quote  # Added for URI encoding


# Load Excel data (assuming pandas can read your file)
df = pd.read_excel("/content/Cleaned_Online_Retail.xlsx")
# reading the dataset
df.head()
df.info()

#preprocessing
# dropping cancelations and null customers
df = df[~  ((df["InvoiceNo"].str.startswith("C")) | (df["CustomerID"].isna())) ]

# dropping the duplicate rows
df.drop_duplicates(inplace=True)


# Removing negative quantities

df = df_clean[df_clean['Quantity'] > 0]



#KG Construction 
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import pandas as pd

# Define namespaces
EX = Namespace("http://example.org/OnlineRetail#")
SCHEMA = Namespace("http://schema.org/")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")

def sanitize_uri_component(value):
    """Replace invalid URI characters with underscores"""
    return str(value).strip().replace(" ", "_").replace("/", "-").replace(",", "")

def xlsx_to_rdf(input_xlsx, output_ttl='online_retail.ttl'):
    # Create RDF graph
    g = Graph()
    g.bind("ex", EX)
    g.bind("xsd", XS)
    g.bind("schema", SCHEMA)

    # Read Excel file
    df = pd.read_excel(input_xlsx, engine='openpyxl')

    for _, row in df.iterrows():
        # Skip rows with missing essential data
        if pd.isna(row.get('InvoiceNo')) or pd.isna(row.get('StockCode')):
            continue

        # Sanitize and create URIs
        invoice_no = sanitize_uri_component(row['InvoiceNo'])
        stock_code = sanitize_uri_component(row['StockCode'])

        invoice_uri = URIRef(EX[f"Invoice_{invoice_no}"])
        product_uri = URIRef(EX[f"Product_{stock_code}"])
        invoice_line_uri = URIRef(EX[f"InvoiceLine_{invoice_no}_{stock_code}"])

        # Add Invoice
        g.add((invoice_uri, RDF.type, EX.Invoice))
        g.add((invoice_uri, EX.invoiceID, Literal(invoice_no)))

        # Add InvoiceDate
        if not pd.isna(row.get('InvoiceDate')):
            try:
                dt = row['InvoiceDate'].to_pydatetime().isoformat()
                g.add((invoice_uri, EX.invoiceDate, Literal(dt, datatype=XSD.dateTime)))
            except AttributeError:
                pass

        # Add Product
        g.add((product_uri, RDF.type, EX.Product))
        g.add((product_uri, EX.stockCode, Literal(stock_code)))

        if not pd.isna(row.get('Description')):
            g.add((product_uri, EX.description, Literal(str(row['Description']).strip())))

        if not pd.isna(row.get('UnitPrice')):
            try:
                g.add((product_uri, EX.unitPrice, Literal(float(row['UnitPrice']), datatype=XSD.decimal)))
            except ValueError:
                pass

        # Add Person
        if not pd.isna(row.get('CustomerID')):
            customer_id = str(row['CustomerID']).strip()
            person_uri = URIRef(EX[f"Person_{customer_id}"])

            g.add((person_uri, RDF.type, EX.Person))
            g.add((person_uri, EX.personID, Literal(customer_id)))

            if not pd.isna(row.get('Country')):
                g.add((person_uri, EX.country, Literal(str(row['Country']).strip())))

            g.add((invoice_uri, EX.customer, person_uri))

        # Add InvoiceLine
        g.add((invoice_line_uri, RDF.type, EX.InvoiceLine))

        if not pd.isna(row.get('Quantity')):
            try:
                g.add((invoice_line_uri, EX.quantity, Literal(int(row['Quantity']), datatype=XSD.integer)))
            except ValueError:
                pass

        g.add((invoice_line_uri, EX.refersToProduct, product_uri))
        g.add((invoice_line_uri, EX.isPartOfInvoice, invoice_uri))
        g.add((invoice_uri, EX.hasInvoiceLine, invoice_line_uri))

    # Save the graph
    g.serialize(destination=output_ttl, format='turtle')
    print(f"Knowledge graph saved to {output_ttl}")



# Usage
xlsx_to_rdf('/content/Cleaned_Online_Retail.xlsx')

from rdflib import Graph

# Load the TTL file
g = Graph()
g.parse("online_retail.ttl", format="turtle")

# Print summary information
print("Total number of triples:", len(g))

# List distinct namespaces
print("Namespaces in the graph:")
for prefix, namespace in g.namespaces():
    print(f"{prefix}: {namespace}")

# Get distinct subjects, predicates, and objects counts
subjects = set(g.subjects())
predicates = set(g.predicates())
objects = set(g.objects())

print("Number of distinct subjects:", len(subjects))
print("Number of distinct predicates:", len(predicates))
print("Number of distinct objects:", len(objects))

# Optional: Execute a SPARQL query to list all classes (rdf:type statements)
query = """
    SELECT DISTINCT ?class
    WHERE { ?s rdf:type ?class }
"""
for row in g.query(query):
    print("Class:", row[0])

#Extract Person Entities with Full Context
from rdflib import Graph, URIRef

# Namespace setup
ns = {"ex": "http://example.org/OnlineRetail#"}
person_class = URIRef(ns["ex"] + "Person")

# Get all unique persons
person_uris = set(g.subjects(predicate=URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                           object=person_class))
def get_person_profile(person_uri):
    person_id = g.value(person_uri, EX.personID)
    country = g.value(person_uri, EX.country)

    profile = f"Customer {person_id} from {country} purchased:\n"

    # Get all invoices linked to this person
    invoices = g.subjects(EX.customer, person_uri)

    for invoice in invoices:
        # Get all invoice lines in each invoice
        invoice_lines = g.objects(invoice, EX.hasInvoiceLine)
        for line in invoice_lines:
            product = g.value(line, EX.refersToProduct)
            quantity = g.value(line, EX.quantity)
            description = g.value(product, EX.description)

            if description:  # Skip if no description
                try:
                    quantity = int(str(quantity))
                    profile += f"- {quantity}x {description}\n"
                except (ValueError, TypeError):
                    profile += f"- {description}\n"

    return profile
person_uris

from rdflib import URIRef
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
# Define namespaces
EX = Namespace("http://example.org/OnlineRetail#")
SCHEMA = Namespace("http://schema.org/")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")
# Construis l’objet URIRef à partir de la chaîne
person_uri = URIRef("http://example.org/OnlineRetail#Person_12553")

# Appelle la fonction avec l’URIRef, pas une chaîne
profile = get_person_profile(person_uri)

print(profile)
text= [ get_person_profile(person) for person in person_uris]
text
from transformers import BertTokenizer, BertModel
import torch
import pandas as pd
from tqdm import tqdm

# --------------------------------------------------
# 1. Prepare text profiles from Knowledge Graph
# --------------------------------------------------
# person_uris: list of KG entities
# get_person_profile(person): returns a textual profile (string)

texts = [get_person_profile(person) for person in person_uris]

# Optional: keep IDs
person_ids = [str(person).split("#")[-1] for person in person_uris]

# --------------------------------------------------
# 2. Load BERT
# --------------------------------------------------
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")
model.eval()

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# --------------------------------------------------
# 3. Generate BERT embeddings
# --------------------------------------------------
embeddings = []

for text in tqdm(texts, desc="Encoding customer profiles"):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

        # [CLS] token embedding (recommended for clustering)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # shape: [1, 768]
        embeddings.append(cls_embedding.cpu().numpy().flatten())

# --------------------------------------------------
# 4. Convert to DataFrame
# --------------------------------------------------
bert_embeddings = pd.DataFrame(embeddings)
bert_embeddings["PersonID"] = person_ids

# --------------------------------------------------
# 5. Save embeddings
# --------------------------------------------------
bert_embeddings.to_csv("bert_embeddings_from_KG_profiles.csv", index=False)

print("✅ BERT embeddings extracted from KG textual profiles and saved.")
import pandas as pd

df = pd.read_csv("bert_embeddings_from_KG_profiles.csv")

customer_ids = df["PersonID"].values
embeddings = df.drop(columns=["PersonID"]).values
