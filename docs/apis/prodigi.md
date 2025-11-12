Published Time: Fri, 07 Nov 2025 15:21:00 GMT

Introduction – Prodigi API Documentation

*   [Introduction](https://www.prodigi.com/print-api/docs/reference/#introduction)
    
    *   [Getting started](https://www.prodigi.com/print-api/docs/reference/#introduction-getting-started)
*   [Environments](https://www.prodigi.com/print-api/docs/reference/#environments)
    
    *   [Sandbox](https://www.prodigi.com/print-api/docs/reference/#environments-sandbox)
    *   [Live](https://www.prodigi.com/print-api/docs/reference/#environments-live)
*   [Authentication](https://www.prodigi.com/print-api/docs/reference/#authentication)
    
*   [Orders](https://www.prodigi.com/print-api/docs/reference/#orders)
    
    *   [Order object](https://www.prodigi.com/print-api/docs/reference/#order-object)
    *   [Create order](https://www.prodigi.com/print-api/docs/reference/#create-order)
    *   [Get order by ID](https://www.prodigi.com/print-api/docs/reference/#get-order-by-id)
    *   [Get orders](https://www.prodigi.com/print-api/docs/reference/#get-orders)
*   [Order actions](https://www.prodigi.com/print-api/docs/reference/#order-actions)
    
    *   [Get actions](https://www.prodigi.com/print-api/docs/reference/#get-actions)
    *   [Cancel an order](https://www.prodigi.com/print-api/docs/reference/#cancel-an-order)
    *   [Pause an order](https://www.prodigi.com/print-api/docs/reference/#pause-an-order)
    *   [Update shipping method](https://www.prodigi.com/print-api/docs/reference/#update-shipping-method)
    *   [Update recipient](https://www.prodigi.com/print-api/docs/reference/#update-recipient)
    *   [Update metadata](https://www.prodigi.com/print-api/docs/reference/#update-metadata)
*   [Quotes](https://www.prodigi.com/print-api/docs/reference/#quotes)
    
    *   [Quote object](https://www.prodigi.com/print-api/docs/reference/#quote-object)
    *   [Create Quote](https://www.prodigi.com/print-api/docs/reference/#create-quote)
*   [Product details](https://www.prodigi.com/print-api/docs/reference/#product-details)
    
    *   [Product Details object](https://www.prodigi.com/print-api/docs/reference/#product-details-object)
    *   [Get Product Details](https://www.prodigi.com/print-api/docs/reference/#get-product-details)
    *   [Get photobook spine details](https://www.prodigi.com/print-api/docs/reference/#get-photobook-spine-details)
*   [Callbacks](https://www.prodigi.com/print-api/docs/reference/#callbacks)
    
    *   [Properties](https://www.prodigi.com/print-api/docs/reference/#callbacks-properties)
*   [ID format](https://www.prodigi.com/print-api/docs/reference/#id-format)
    
*   [Outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes)
    
    *   [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes)
*   [Status](https://www.prodigi.com/print-api/docs/reference/#status)
    
    *   [Status object](https://www.prodigi.com/print-api/docs/reference/#status-status-object)
*   [Errors](https://www.prodigi.com/print-api/docs/reference/#errors)
    
    *   [Base error object](https://www.prodigi.com/print-api/docs/reference/#errors-base-error-object)
    *   [TraceParent](https://www.prodigi.com/print-api/docs/reference/#errors-traceparent)
    *   [Generic errors](https://www.prodigi.com/print-api/docs/reference/#errors-generic-errors)
*   [The order process](https://www.prodigi.com/print-api/docs/reference/#the-order-process)
    
    *   [1\. Order creation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-1-order-creation)
    *   [2\. Assets download](https://www.prodigi.com/print-api/docs/reference/#the-order-process-2-assets-download)
    *   [3\. Lab allocation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-3-lab-allocation)
    *   [4\. Asset preparation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-4-asset-preparation)
    *   [5\. Lab submission](https://www.prodigi.com/print-api/docs/reference/#the-order-process-5-lab-submission)
    *   [6\. Production](https://www.prodigi.com/print-api/docs/reference/#the-order-process-6-production)
    *   [7\. Shipping](https://www.prodigi.com/print-api/docs/reference/#the-order-process-7-shipping)
    *   [8\. Order completion](https://www.prodigi.com/print-api/docs/reference/#the-order-process-8-order-completion)
    *   [Image retention](https://www.prodigi.com/print-api/docs/reference/#the-order-process-image-retention)
*   [Help & support](https://www.prodigi.com/print-api/docs/reference/#help-amp-support)
    
    *   [Contact](https://www.prodigi.com/print-api/docs/reference/#help-amp-support-contact)
    *   [Guides](https://www.prodigi.com/print-api/docs/reference/#help-amp-support-guides)
    *   [Versions](https://www.prodigi.com/print-api/docs/reference/#help-amp-support-versions)
*   [Sign up for an API Key](https://dashboard.prodigi.com/register "Sign up for an API key")
    

# Welcome to the Prodigi API reference documentation for v4

# [Sign up for your free API key](https://dashboard.prodigi.com/register "Sign up for your free API key") Introduction

Our RESTful API is built using standard HTTP response codes, authentication and verbs. We accept `application/json` payloads, and return `JSON` on every response.

## Getting started

Our [guide to placing your first order](https://www.prodigi.com/blog/your-first-print-api-order/ "Your first Prodigi API order") walks through our order process, from authentication to submitting an order to our print network.

# Environments

We have two environments: **Sandbox** and **Live**. Creating a new account on the [Live Dashboard](https://dashboard.prodigi.com/ "Live production dashboard") will automatically set up both a Sandbox and Live account.

## Sandbox

Sandbox is our **testing** environment. It **will not fulfil your orders**, and you will **not be charged** for using it.

*   Sandbox API: **api.sandbox.prodigi.com**
*   Sandbox dashboard: [sandbox-beta-dashboard.pwinty.com](https://sandbox-beta-dashboard.pwinty.com/ "Sandbox dashboard")

## Live

Live is our **production** environment. Any orders that are placed here **will be produced and shipped**.

*   Live API: **api.prodigi.com**
*   Live dashboard: [dashboard.prodigi.com](https://dashboard.prodigi.com/ "Production dashboard")

# Authentication

Using the authentication header

Copy to clipboard

```
curl "https://api.prodigi.com/v4.0/Orders" \
  -X GET \
  -H "X-API-Key: your-api-key"
```

Each request to our API requires the use of an authentication header: `X-API-Key`.

You can obtain an API key by [signing up for a free Prodigi account](https://dashboard.prodigi.com/register "Sign up for Prodigi").

# Your API credentials may differ between Sandbox and Live. If you have issues authenticating, please ensure you are using the correct credentials for that environment. Orders

Creating an order is a single API request, supplying all of the relevant information. Once the order is in our system, we will process it according to your account settings, taking into account any configured pause window. Otherwise, we will start to fulfill it immediately.

## Order object

Order object

Copy to clipboard

```
{
    "id": "ord_840796",
    "created": "2021-03-11T14:31:23.41Z",
    "lastUpdated": "2021-03-11T14:31:23.4931606Z",
    "callbackUrl": null,
    "merchantReference": "MyMerchantReference1",
    "shippingMethod": "Overnight",
    "idempotencyKey": null,
    "status": {
        "stage": "InProgress",
        "issues": [],
        "details": {
            "downloadAssets": "NotStarted",
            "printReadyAssetsPrepared": "NotStarted",
            "allocateProductionLocation": "NotStarted",
            "inProduction": "NotStarted",
            "shipping": "NotStarted"
        }
    },
    "charges": [],
    "shipments": [],
    "recipient": {
        "name": "Mr test",
        "email": null,
        "phoneNumber": null,
        "address": {
            "line1": "14 test place",
            "line2": "test",
            "postalOrZipCode": "12345",
            "countryCode": "US",
            "townOrCity": "somewhere",
            "stateOrCounty": null
        }
    },
    "branding": {
        "postcard": { "url" : "https://sample/postcard.jpg"},
        "flyer": { "url" : "https://sample/flyer.pdf"},
        "packing_slip_bw": { "url" : "https://sample/delivery_note_bw.jpg"},
        "packing_slip_color" : { "url" : "https://sample/delivery_note_color.jpg"},
        "sticker_exterior_round" : { "url" : "https://sample/sticker_round.jpg"},
        "sticker_exterior_rectangle"  :{ "url" : "https://sample/sticker_rect.jpg"},
        "sticker_interior_round" : { "url" : "https://sample/sticker_round.jpg"},
        "sticker_interior_rectangle": { "url" : "https://sample/sticker_rect.jpg"}
    },
    "items": [
        {
            "id": "ori_926886",
            "status": "NotYetDownloaded",
            "merchantReference": "item #1",
            "sku": "GLOBAL-CFPM-16X20",
            "copies": 1,
            "sizing": "fillPrintArea",
            "attributes": {
                "color": "black"
            },
            "assets": [
                {
                    "id": "ast_114059",
                    "printArea": "default",
                    "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                    "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                    "pageCount": 50,
                    "status": "InProgress"
                }
            ],
            "recipientCost": {
                "amount": "10.74",
                "currency": "GBP"
            }
        }
    ],
    "packingSlip": null,
    "metadata": {
        "mycustomkey": "some-guid",
        "someCustomerPreference": {
            "preference1": "something",
            "preference2": "red"
        },
        "sourceId": 12345
    }
```

The Order object contains all the information you need to manage your order. Once created, most of the order remains static, while areas like Status and Shipments change [as the order progresses](https://www.prodigi.com/print-api/docs/reference/#the-order-process "The order process").

### Top level

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | n/a | The order's unique ID. Set by Prodigi. |
| `created` | string | n/a | The UTC DateTime the order was created. Set by Prodigi. |
| `callbackUrl` | string | no | Your callback URL, where we send [callback events](https://www.prodigi.com/print-api/docs/reference/#callbacks "Callbacks"). |
| `merchantReference` | string | no | Your own reference ID for this order. |
| `shippingMethod` | string | yes | Your requested shipping method: either `Budget`, `Standard`, `StandardPlus`, `Express` or `Overnight`. See [shipping](https://www.prodigi.com/print-api/docs/reference/#the-order-process-7-shipping) for more information about these methods, and how they map to real-world couriers. |
| `idempotencyKey` | string | no | Your personal [idempotency key](https://www.prodigi.com/print-api/docs/reference/#order-object-idempotency-key "About idempotency keys"). |
| `status` | [Status](https://www.prodigi.com/print-api/docs/reference/#status "Order statuses") | n/a | The overall status of the order. Set by Prodigi. |
| `charges` | array of [Charges](https://www.prodigi.com/print-api/docs/reference/#order-object-charge "Order charges") | n/a | Charges for this order. Set by Prodigi. |
| `shipments` | array of [Shipments](https://www.prodigi.com/print-api/docs/reference/#order-object-shipment "Order shipments") | n/a | Courier and service shipment details per item, if available. Set by Prodigi. |
| `recipient` | [Recipient](https://www.prodigi.com/print-api/docs/reference/#order-object-recipient "Order recipient") | yes | Shipping name and address. |
| `branding` | [Branding](https://www.prodigi.com/print-api/docs/reference/#order-object-branding "Order branding") | no | Per-order branding components. |
| `items` | array of [Items](https://www.prodigi.com/print-api/docs/reference/#order-object-item "Order items") | yes | Items to be fulfilled (products + assets). |
| `packingSlip` | [PackingSlip](https://www.prodigi.com/print-api/docs/reference/#order-object-packing-slip "Packing slip object") | no | Packing slip. |
| `metadata` | hashtable | no | A custom json object containing keys and values of your choice. Up to 2000 characters. |

### Recipient

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Recipient's name. Very long name strings may be truncated to suit courier guidelines. |
| `email` | string | no | Recipient's email address |
| `phoneNumber` | string | no | Recipient's mobile phone number |
| `address` | [Address](https://www.prodigi.com/print-api/docs/reference/#order-object-address "Order address") | yes | Recipient's address. |
| While recipient `email` and `phoneNumber` are technically optional, it's highly recommended you include these if you have international orders as they aid couriers with customs issues. For example, contact information is a requirement for any item shipped from the UK. Where necessary, we will substitute with default information if not provided to ensure courier systems accept the order, but relying on this is not advisable. |  |  |  |

### Address

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `line1` | string | yes | First line of recipient's address. |
| `line2` | string | no | Second line of recipient's address. |
| `postalOrZipCode` | string | yes | Postcode or zip code of recipient's address. |
| `countryCode` | string | yes | Two-letter [ISO country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes "ISO country code list") of recipient's address. |
| `townOrCity` | string | yes | Town or city of recipient's address. |
| `stateOrCounty` | string | no | State or county for the recipient's address. |

### Branding

The `branding` object allows you to specify one or more branded assets (e.g. postcards, flyers, stickers, and packing slips) that will be included in the shipment. Each item must be supplied as a URL pointing to a publicly accessible asset.

Additional file setup details including pricing for each item can be found within your [Prodigi account](https://dashboard.prodigi.com/settings/branding).

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `postcard` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | A6 branded card to include inside the package |
| `flyer` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | A5 insert for additional branding or messaging |
| `packing_slip_bw` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Black & white packing slip |
| `packing_slip_color` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Full colour packing slip |
| `sticker_exterior_round` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Round sticker on external packaging |
| `sticker_exterior_rectangle` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Rectangular sticker on external packaging |
| `sticker_interior_round` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Round sticker applied inside the package |
| `sticker_interior_rectangle` | [BrandingAsset](https://www.prodigi.com/print-api/docs/reference/#branding-asset "Branding asset") | No | Rectangular sticker applied inside the package |

### Branding asset

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `url` | string | Yes | A publicly accessible URL pointing to print-ready assets. Each asset will be validated for format and quality. |

### Charge

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | n/a | Unique ID for this charge. Set by Prodigi. |
| `chargeType` | string | n/a | The type of charge record provided this could be one of the following: `Item`, `Shipping`, `Refund` or `Other`. |
| `prodigiInvoiceNumber` | string | n/a | Depending on your billing frequency, this will be your Prodigi Invoice Number or null. Set by Prodigi. |
| `totalCost` | [Cost](https://www.prodigi.com/print-api/docs/reference/#order-object-cost "Order cost object") | n/a | Total of all individual charges. Set by Prodigi. |
| `items` | array of [ChargeItems](https://www.prodigi.com/print-api/docs/reference/#order-object-charge-item "Charge item object") | n/a | Individual items associated with this charge. Set by Prodigi. |

### Cost

A generic field that represents the debit or credit for a given item.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `amount` | string | n/a | Amount charged. Positive is debit, negative is credit. Set by Prodigi. |
| `currency` | string | n/a | Three-letter [ISO currency code](https://en.wikipedia.org/wiki/ISO_4217 "List of currency codes") for this amount. Set by Prodigi. |

### Charge item

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | n/a | Unique ID for this charge item. Set by Prodigi. |
| `shipmentId` | string | n/a | Shipment ID for the charge item, or null for product charge items. Set by Prodigi. |
| `itemId` | string | n/a | Item ID, corresponding to the array of items at the top of the order. Null for shipping charge items. Set by Prodigi. |
| `cost` | [Cost](https://www.prodigi.com/print-api/docs/reference/#order-object-cost "Cost object") | n/a | Cost breakdown for this item. Set by Prodigi. |

### Shipment

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | n/a | Unique ID for this shipment. Set by Prodigi. |
| `status` | string | n/a | A status indicator for the shipment expected values are: `Processing` The shipment has yet to be shipped, `Cancelled` the shipment has been cancelled and `Shipped` The shipment has been shipped. |
| `carrier` | carrier | n/a | Carrier for this shipment. Set by Prodigi. |
| `tracking` | tracking | n/a | Tracking information for this shipment. Only be set if an shipment can be tracked. Set by Prodigi. |
| `dispatchDate` | datetime | n/a | When the lab despatched this shipment. Set by Prodigi. |
| `items` | array of [Shipment Items](https://www.prodigi.com/print-api/docs/reference/#order-shipment-item "Shipment Item object") | n/a | Helps identify the items in this shipment. Set by Prodigi. |
| `tracking` | [tracking](https://www.prodigi.com/print-api/docs/reference/#order-object-tracking "Tracking object") | n/a | Url and number of tracking information. |
| `fulfillmentLocation` | [fulfillmentLocation](https://www.prodigi.com/print-api/docs/reference/#order-object-fulfillment-location "Order fulfillment location object") | n/a | Country and lab fulfilling the shipment. |

### Shipment Item

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `itemId` | string | n/a | Unique ID for the item that is included as part of the shipment. Set by Prodigi. |

### Fulfillment location

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `countryCode` | string | n/a | The two-letter [ISO country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes "ISO country code list") from where the items will be fulfilled. |
| `labCode` | string | n/a | The identifying code of the lab fulfilling the items. |

### Tracking

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `url` | string | n/a | A Url that will provide shipment status via a 3rd party tracking service. |
| `number` | string | n/a | The shipment carriers tracking number. |

### Item

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | n/a | Unique ID for this order item. Set by Prodigi. |
| `status` | string | n/a | A status indicator for the item expected values are: `Ok` nothing wrong with this item, `Invalid` one or more assets have failed to download and `NotYetDownloaded` the assets associated with this item are yet to be downloaded. |
| `merchantReference` | string | no | Your personal reference for this item. |
| `sku` | string | yes | The Prodigi SKU of the product. Use the lookups endpoints to find out more information on each SKU. |
| `copies` | integer | yes | Quantity of items |
| `sizing` | string | yes | The sizing strategy for us to use. The value should be one of `fillPrintArea`, `fitPrintArea` or `stretchToPrintArea`. More information can be found in our [image resizing section](https://www.prodigi.com/print-api/docs/reference/#order-object-image-resizing "Image resizing"). |
| `recipientCost` | [Cost](https://www.prodigi.com/print-api/docs/reference/#order-object-cost "Cost") | no | The price you charged the recipient for these items. While not required, it's highly recommended if you have international orders as it aids shipping companies with customs issues. |
| `attributes` | hashtable | no | Product attributes, such as a frame colour. Use the lookups endpoints to find a product's available attributes. |
| `assets` | array of [Assets](https://www.prodigi.com/print-api/docs/reference/#order-object-asset "Order asset object") | yes | File assets for this order item, i.e. the image file(s). |

### Asset

An Asset is an image belonging to a product. Our products support zero, one or many images per item, and the item's `assets` array determines the location of each image on the product. For a full list of which assets a given product supports, use the product lookup endpoint.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `printArea` | string | yes | Name of the assets print area. Default value is `default`. Examples of other print areas include `spine` (for photobooks) and `lid` (for jigsaws). |
| `status` | string | n/a | The status of the asset in terms of availability to be processed in production. Values are `complete` the asset has been downloaded for production, `inProgress` the asset is yet to be downloaded and `error` there has been a problem downloading the asset. |
| `url` | string | yes | URL of the asset. |
| `thumbnailUrl` | string | yes | URL of the item asset. Please not this may not be present until after the asset has been downloaded and the item allocated a shipment. |
| `md5Hash` | string | no | If supplied then the image file will be used to generate a corresponding hash that must match this. |
| `pageCount` | integer | no | Not required by default, but is required when creating orders containing products where additional page pricing is applied - for example: photobooks. |

### Packing slip

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `url` | string | no | URL of the packing slip file |
| `status` | string | no | Status of the packing slip. Set by Prodigi. |

### Idempotency key

The`idempotencyKey` is an optional property that can help us determine if your order is a duplicate of an earlier order. If not supplied, the order will not be checked for duplicates.

Most merchants can guarantee that we will only receive one request for one order, so the idempotency key would not be required. For others who may be running distributed systems where it can be harder to guarantee a single request for a single order, the use of the `idempotencyKey` is recommended: a string that is unique to this order.

While the idempotency key can be a simple string, we recommended that you use a GUID of some form to avoid clashes. We remember all your idempotency keys indefinitely, so you need a key of sufficient complexity.

Internally, the idempotency key is scoped to your account, so another merchant's key will never conflict with yours.

We use `idempotencyKey` to check for duplicates rather than `merchantReference` as it's not uncommon for merchants to order reprints of an order using the same `merchantReference`.

### Image resizing

If your image does not fit the product size, by default we will crop your image centrally. We print the image as large as possible, removing the top/bottom or left/right parts of the image that go beyond the print area.

However, you can also specify a sizing parameter to change this behaviour.

| Sizing mode | Default? | Description |
| --- | --- | --- |
| `fillPrintArea` | yes | Your image will be centred and cropped so that it exactly fits the aspect ratio (height divided by width) of the printing area of the product you chose. Your image will cover all of the product print area. |
| `fitPrintArea` | no | Your image will be shrunk until the whole image fits within the print area of the product, whilst retaining the aspect ratio of your image. This will usually mean there is white space at the top/bottom or left/right edges. |
| `stretchToPrintArea` | no | Your image will be resized so that it completely fills the print area of the product. If the aspect ratio of your image is different to that of the printing area, your image will be stretched or squashed to fit. |

### Rotation

Pwinty will automatically try to rotate your images so that they need the least possible resizing to fit the product size. For example, if you are creating a 10 x 15 photo, and upload an image that is 4500px x 3000px, then Pwinty will flip it round so it is 3000px x 4500px and thus fits the photo perfectly.

## Create order

POST/v4.0/orders

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/Orders" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '
    {
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Overnight",
        "recipient": {
            "name": "Mr Testy McTestface",
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "branding": {
            "postcard": { "url" : "https://sample/postcard.jpg"},
            "flyer": { "url" : "https://sample/flyer.pdf"},
            "packing_slip_bw": { "url" : "https://sample/delivery_note_bw.jpg"},
            "packing_slip_color" : { "url" : "https://sample/delivery_note_color.jpg"},
            "sticker_exterior_round" : { "url" : "https://sample/sticker_round.jpg"},
            "sticker_exterior_rectangle"  :{ "url" : "https://sample/sticker_rect.jpg"},
            "sticker_interior_round" : { "url" : "https://sample/sticker_round.jpg"},
            "sticker_interior_rectangle": { "url" : "https://sample/sticker_rect.jpg"}
        },
        "items": [
            {
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "recipientCost": {
                    "amount": "15.00",
                    "currency": "USD"
                },
                "assets": [
                    {
                        "printArea": "default",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "pageCount": 50
                    }
                ]
            }
        ],
        "metadata": {
            "mycustomkey":"some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    }
  '
```

Response

Copy to clipboard

```
{
    "outcome": "Created",
    "order": {
        "id": "ord_840797",
        "created": "2021-03-11T14:40:05.12Z",
        "lastUpdated": "2021-03-11T14:40:05.2018442Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Overnight",
        "idempotencyKey": null,
        "status": {
            "stage": "InProgress",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr Test",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "branding": {
            "postcard": { "url" : "https://sample/postcard.jpg"},
            "flyer": { "url" : "https://sample/flyer.pdf"},
            "packing_slip_bw": { "url" : "https://sample/delivery_note_bw.jpg"},
            "packing_slip_color" : { "url" : "https://sample/delivery_note_color.jpg"},
            "sticker_exterior_round" : { "url" : "https://sample/sticker_round.jpg"},
            "sticker_exterior_rectangle"  :{ "url" : "https://sample/sticker_rect.jpg"},
            "sticker_interior_round" : { "url" : "https://sample/sticker_round.jpg"},
            "sticker_interior_rectangle": { "url" : "https://sample/sticker_rect.jpg"}
        },
        "items": [
            {
                "id": "ori_926887",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "mycustomkey": "some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    },
    "traceParent": "00-f68685c43545e048bc44d9bc8239d59a-967255597477ac40-00"
}
```

POSTing to the `/orders` endpoint submits and creates your order in Prodigi.

Once an order is submitted and any configured order pause window expires, it begins the [process of fulfillment](https://www.prodigi.com/print-api/docs/reference/#the-order-process "The order process").

Where an order has been submitted and is paused only the order ID is returned in the initial response, with the order status being set to "on hold". For orders in this state, you can continue to make updates to the order via the Prodigi dashboard. Once the pause window expires, a web-hook is triggered containing the full order details.

Please refer to the [Order actions](https://www.prodigi.com/print-api/docs/reference/#order-actions "Order actions") section on more information about updating existing orders. Once an order passes into fulfilment, it can no longer be changed or cancelled.

### Create order outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `created` | 200 | Order created. |
| `onHold` | 200 | Order created on hold due to order edit window preference. |
| `createdWithIssues` | 200 | Order created but contains issues that need fixing. |
| `alreadyExists` | 200 | Order with the same idempotency key already exists. The new order has not been created, and we have returned the existing order. |

## Get order by ID

GET/v4.0/orders/{prodigi\_order\_id}

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/orders/ord_677258" \
  -X GET \
  -H "X-API-Key: your-api-key"
```

Response

Copy to clipboard

```
{
    "outcome": "Ok",
    "order": {
        "id": "ord_840797",
        "created": "2021-03-11T14:40:05.12Z",
        "lastUpdated": "2021-03-11T14:40:05.203Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Overnight",
        "idempotencyKey": null,
        "status": {
            "stage": "InProgress",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr Test",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "items": [
            {
                "id": "ori_926887",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "pageCount": 50,
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "mycustomkey": "some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    },
    "traceParent": "00-ef2d62064c7b224690a9578e84f4c617-150bbac7b6406e46-00"
}
```

This endpoint returns an [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") for a given Prodigi order ID where the order has been submitted for fulfilment and any configured pause window has expired.

### Get Order by ID Outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `ok` | 200 | The request was understood and a relevant response was returned. |

## Get orders

GET/v4.0/orders

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/orders" \
  -X GET \
  -H "X-API-Key: your-api-key"
```

This endpoint returns a list of [Orders](https://www.prodigi.com/print-api/docs/reference/#order-object) for the given filtering options.

All of these options are optional. If none are provided, their defaults will be used. Results are sorted by Prodigi order ID (descending).

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `top` | int | 10 | Number of orders to return. Must be 1–100. |
| `skip` | int | 0 | Number of records to skip before the next `top` worth of orders. Must be greater than or equal to 0. |
| `createdFrom` | datetime | null | Limit to orders placed after this date/time (UTC). Can be used without `createdTo`. |
| `createdTo` | datetime | null | Limit to orders placed before this date/time (UTC). Can be used without `createdFrom`. |
| `status` | string | null | Limit to a particular status. Valid `status` values are `draft`, `awaitingPayment`, `inProgress`, `complete`, `cancelled`. |
| `orderIds` | array | null | Limit to a list of Prodigi order IDs. |
| `merchantReferences` | array | null | Limit to a range of your order references. |

### Response

Response

Copy to clipboard

```
{
    "outcome": "Ok",
    "orders": [
        {
            "id": "ord_840797",
            // rest of the order
        },
        {
            "id": "ord_839555",
            // rest of the order
        },
        {
            "id": "ord_838659",
            // rest of the order
        },
        {
            "id": "ord_838055",
            // rest of the order
        }
    ],
    "hasMore": true,
    "nextUrl": "https://api.sandbox.prodigi.com/v4.0/Orders?Skip=10",
    "traceParent": "00-cb879e84d8c70a45b5742d34be5f3a6d-4535bc8797a33c49-00"
}
```

| Name | Type | Description |
| --- | --- | --- |
| `orders` | array of [Orders](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") | Each `order` is identical to that returned by [Get Order by ID](https://www.prodigi.com/print-api/docs/reference/#get-order-by-id "Get order by ID"). |
| `hasMore` | boolean | True if there are more results available. |
| `nextUrl` | string | If `HasMore` is true, contains the full URL to the next page of orders. |

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `ok` | 200 | The request was understood and a relevant response was returned. |

# Order actions

## Get actions

GET/v4.0/orders/{prodigi\_order\_id}/actions

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/Orders/ord_123456/actions" \
  -X GET \
  -H "X-API-Key: your-api-key"
```

Response

Copy to clipboard

```
{
    "outcome": "Ok",
    "cancel": {
        "isAvailable": "Yes"
    },
    "changeRecipientDetails": {
        "isAvailable": "Yes"
    },
    "changeShippingMethod": {
        "isAvailable": "Yes"
    },
    "changeMetaData": {
        "isAvailable": "Yes"
    },
    "traceParent": "00-e5bcd15ebc235043bf43b6fb209de64e-72320d4625a34a40-00"
}
```

There are 4 actions you can take against an order before it is in fulfilment:

*   Cancel
*   Update shipping method
*   Update recipient details
*   Update metadata

You can find out which actions are currently valid for a given order by sending a GET request to the order's `actions` endpoint: `Orders/{prodigi_order_id}/actions`.

### Request parameters

| Parameter | Description |
| --- | --- |
| `prodigi_order_id` | The Prodigi ID of the order. |

### Response

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `ok` | 200 | The request was understood and a relevant response was returned. |

## Cancel an order

POST/v4.0/orders/{prodigi\_order\_id}/actions/cancel

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/orders/ord_123456/actions/cancel" \
  -X POST \
  -H "X-API-Key: your-api-key"
```

Response

Copy to clipboard

```
{
    "outcome": "Cancelled",
    "order": {
        "id": "ord_840797",
        "created": "2021-03-11T14:40:05.12Z",
        "lastUpdated": "2021-03-11T15:04:08.0923435Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Overnight",
        "idempotencyKey": null,
        "status": {
            "stage": "Cancelled",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr Test",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "items": [
            {
                "id": "ori_926887",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "mycustomkey": "some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    },
    "traceParent": "00-fd6711a9793bd648b0f83300e73dcd10-0eefc6d035357d42-00"
}
```

Sending a POST request to the `actions/cancel` endpoint for a specific `prodigi_order_id` attempts to cancel the entire order.

Where an order is not yet in fulfilment, the full order will be refunded. Once an order is in fulfilment, and any configured pause window has expired, the shipping charge will be refunded, in line with our [terms and conditions](https://www.prodigi.com/terms-and-conditions/).

If all of the items in the order are cancelled, the resulting returned order will have a status of `cancelled` and all of its shipments will likewise show `cancelled: true`.

If, however, we are only able to cancel some of the items, the resulting order will not have a `cancelled` status and the uncancelled shipments will have `cancelled: false`.

### Request parameters

| Parameter | Description |
| --- | --- |
| `prodigi_order_id` | The Prodigi ID of the order to cancel. |

### Cancel order outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `cancelled` | 200 | Order successfully cancelled. |
| `failedToCancel` | 200 | We could not cancel the order. It could be already in production and too late to cancel. |
| `actionNotAvailable` | 200 | Order cannot be cancelled at this time. |

## Pause an order

By default all orders submitted via the Print API will be submitted and sent to fulfilment immediately.

Through the [Prodigi dashboard](https://dashboard.prodigi.com/) you can configure a pause window for all orders to adhere to, either by setting an amount of time for all orders to be paused, or you can configure orders to be paused indefinitely, requiring orders to then be submitted manually through the dashboard.

Once a configured pause window expires, the order will submit for fulfilment and a callback will be sent informing you of this.

## Update shipping method

POST/v4.0/orders/{prodigi\_order\_id}/actions/updateShippingMethod

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/Orders/ord_123456/actions/updateShippingMethod" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -d '{ "shippingMethod": "Budget" }'
```

Response

Copy to clipboard

```
{
    "outcome": "Updated",
    "shippingUpdateResults": [],
    "order": {
        "id": "ord_840799",
        "created": "2021-03-11T15:06:40.697Z",
        "lastUpdated": "2021-03-11T15:06:46.2816154Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Express",
        "idempotencyKey": null,
        "status": {
            "stage": "InProgress",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr Testy McTestface",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "items": [
            {
                "id": "ori_926889",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "mycustomkey": "some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    },
    "traceParent": "00-a80b88df69bd0e45a923cc4d9f858978-5eaad925e38cd348-00"
}
```

### Request parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `prodigi_order_id` | string | yes | Prodigi ID of the order you wish to update. |
| `shipping_method` | string | yes | One of `Budget`, `Standard`, `StandardPlus`, `Express`, `Overnight`. |

### Response object

| Name | Type | Description |
| --- | --- | --- |
| `order` | [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") | The amended order. |
| `shipmentUpdateResults` | array of [ShipmentDetails](https://www.prodigi.com/print-api/docs/reference/#update-shipping-method-shipment-detail-object "Shipment details") | An array of [ShipmentDetails](https://www.prodigi.com/print-api/docs/reference/#update-shipping-method-shipment-detail-object "Shipment details object") objects. |

### ShipmentDetail object

| Name | Type | Description |
| --- | --- | --- |
| `shipmentId` | string | Shipment identifier. |
| `successful` | boolean | Whether the update succeeded. |

### Update shipping method Outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `updated` | 200 | Shipping method updated against the order and all shipments. |
| `partiallyUpdated` | 200 | Shipping method updated against the order and some shipments, but at least one shipment could not be updated. |
| `failedToUpdate` | 200 | No shipments could be updated, so the order has not been updated. |
| `actionNotAvailable` | 200 | We are no longer able to update any shipments, so this action is unavailable. |

## Update recipient

POST/v4.0/orders/{prodigi\_order\_id}/actions/updateRecipient

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/Orders/ord_123456/actions/updateRecipient" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -d '{
        "name": "Mr. Jeff Testing",
        "email": "jeff.testing@test.co.uk",
        "phoneNumber": "123456780",
        "address" : {
                      "line1": "14 test place",
                      "line2": "test",
                      "postalOrZipCode": "12345",
                      "countryCode": "US",
                      "townOrCity": "MyTown",
                      "stateOrCounty": null
                    }
      }'
```

Response

Copy to clipboard

```
{
    "outcome": "Updated",
    "shipmentUpdateResults": [],
    "order": {
        "id": "ord_840799",
        "recipient": {
            "name": "Mr. Jeff Testing",
            "email": "jeff.testing@test.co.uk",
            "phoneNumber": "123456780",
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "MyTown",
                "stateOrCounty": null
            }
        },
        // rest of the order
    },
    "traceParent": "00-e3466ad67db82340aa97a337e5c9ea91-edb742f49fc22c46-00"
}
```

### Request parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `prodigi_order_id` | string | yes | Prodigi ID of the order to update. |
| `recipient` | [Recipient](https://www.prodigi.com/print-api/docs/reference/#update-recipient-recipient-object "Recipient object") | yes | Amended recipient details. |

### Recipient object

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `Name` | string | yes | Full name of the recipient |
| `Email` | string | yes | Recipient's email |
| `PhoneNumber` | string | yes | Recipient's primary contact number |
| `Address` | [Address](https://www.prodigi.com/print-api/docs/reference/#update-recipient-recipient-address-object) | yes | Recipient's address |

### Recipient Address object

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `line1` | string | yes | First line of recipient's address. |
| `line2` | string | yes | Second line of recipient's address. |
| `townOrCity` | string | yes | Town or city of recipient's address. |
| `stateOrCounty` | string | yes | State or county of the recipient's address. |
| `postalOrZipCode` | string | yes | Postcode or zip code of recipient's address. |
| `countryCode` | string | yes | Two-letter ISO country code of recipient's address. |

### Response

| HTTP status code | Description |
| --- | --- |
| `200` | Returns an [UpdateRecipientResponse](https://www.prodigi.com/print-api/docs/reference/#update-recipient-update-recipient-response-object "UpdateRecipientResponse object") object. |
| `400` | Failed to update the recipient, most likely because of an invalid `prodigi_order_id`. |

### UpdateRecipientResponse object

| Name | Type | Description |
| --- | --- | --- |
| `order` | [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") | The amended order. |
| `shipmentResult` | array of [ShipmentDetails](https://www.prodigi.com/print-api/docs/reference/#update-shipping-method-shipment-detail-object "ShipmentDetails object") | An array of [ShipmentDetail](https://www.prodigi.com/print-api/docs/reference/#update-shipping-method-shipment-detail-object "ShipmentDetail object") objects. |
| `result` | string | One of `completed`, `partiallyComplete`, `failed`. |

### ShipmentDetail object

| Name | Type | Description |
| --- | --- | --- |
| `shipmentId` | string | The shipment identifier. |
| `successful` | boolean | Whether the update succeeded. |
| `errorCode` | string | One of `order.shipments.updateFailed`, `order.shipments.invalid`, `order.shipments.notAvailable`. |
| `description` | string | Error code description. |

### Update recipient outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `updated` | 200 | Recipient updated in the order and all shipments. |
| `partiallyUpdated` | 200 | Recipient updated in the order and some shipments, but at least one shipment could not be updated. |
| `failedToUpdate` | 200 | No shipments could be updated so the order has not been updated. |
| `actionNotAvailable` | 200 | We are no longer able to update any shipments, so this action is unavailable. |

## Update metadata

POST/v4.0/orders/{prodigi\_order\_id}/actions/updatemetadata

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/Orders/ord_123456/actions/updateMetadata" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -d '{ 
        "metadata" : { 
            "internalRef" : "abdef",
            "templateSize" : 1,
            "feedback" : {
                "message": "some message",
                "stars": 5
            }
        }
      }'
```

Response

Copy to clipboard

```
{
    "outcome": "Updated",
    "order": {
        "id": "ord_840799",
        "created": "2021-03-11T15:06:40.697Z",
        "lastUpdated": "2021-03-11T15:14:28.9200361Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Express",
        "idempotencyKey": null,
        "status": {
            "stage": "InProgress",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr Test",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "items": [
            {
                "id": "ori_926889",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "internalRef": "abdef",
            "templateSize": 1,
            "feedback": {
                "message": "some message",
                "stars": 5
            }
        }
    },
    "traceParent": "00-0229c7d0a6e3814b98806af95599c00d-c6ba62fadb84e346-00"
}
```

Updating an order's metadata replaces the existing metadata on the order entirely.

You can update an order's `metadata` at any time in order process, including after completion.

### Request parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `prodigi_order_id` | string | yes | Prodigi ID of the order to update. |
| `metadata` | json | yes | Data to replace the current metadata. |

### Response

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `updated` | 200 | Metadata updated successfully. |

# Quotes

The Quote endpoint allows you to get pricing and shipping information about a given set of products without creating an order. It returns how the order will be fulfilled, including:

*   The fulfillment location
*   The cost of the products
*   The cost of shipping
*   The couriers of each shipment

## Quote object

Quote object

Copy to clipboard

```
{
    "outcome": "Ok",
    "quotes": [
        {
            "shipmentMethod": "Budget",
            "costSummary": {
                "items": {
                    "amount": "7.50",
                    "currency": "GBP"
                },
                "shipping": {
                    "amount": "1.50",
                    "currency": "GBP"
                }
            },
            "shipments": [
                {
                    "carrier": {
                        "name": "royalmail",
                        "service": "Standard"
                    },
                    "fulfillmentLocation": {
                        "countryCode": "GB",
                        "labCode": "uk6"
                    },
                    "cost": {
                        "amount": "1.50",
                        "currency": "GBP"
                    },
                    "items": [
                        "qit_cf79d209cf3e40ff8a56861f50d8937a"
                    ]
                }
            ],
            "items": [
                {
                    "id": "qit_cf79d209cf3e40ff8a56861f50d8937a",
                    "sku": "GLOBAL-TECH-IP11P-FC-CP",
                    "copies": 1,
                    "unitCost": {
                        "amount": "7.50",
                        "currency": "GBP"
                    },
                    "attributes": {},
                    "assets": [
                        {
                            "printArea": "default"
                        }
                    ]
                }
            ]
        }
    ]
}
```

The Quote endpoint returns an array of Quotes.

Each Quote provides pricing information for products and shipments based on a specific [shipping method](https://www.prodigi.com/print-api/docs/reference/#create-quote-top-level).

If a `shippingMethod` is specified for a Quote, only that shipping method is returned. If a `shippingMethod` is not specified, a Quote for each of the shipping methods is returned: budget, standard, standard plus, express and overnight.

### Top level

| Property | Type | Description |
| --- | --- | --- |
| `quotes` | array of [Quotes](https://www.prodigi.com/print-api/docs/reference/#quote-object "Quote object") | One quote for each shipping method. |

### Quote

| Property | Type | Description |
| --- | --- | --- |
| `shipmentMethod` | string | Shipping method for this quote. One of `budget`,`standard`, `standardplus`, `express` or `overnight`. |
| `costSummary` | [CostSummary](https://www.prodigi.com/print-api/docs/reference/#quote-object-cost-summary "Cost summary object") | Summary of total costs. |
| `shipments` | array of [Shipments](https://www.prodigi.com/print-api/docs/reference/#quote-object-shipment "Quote shipment object") | Expected courier details, cost and included items. |
| `items` | array of [Items](https://www.prodigi.com/print-api/docs/reference/#quote-object-item "Quote item object") | The order items, with an `id` matching the item in each `shipment`. |

### Cost summary

| Property | Type | Description |
| --- | --- | --- |
| `items` | [Cost](https://www.prodigi.com/print-api/docs/reference/#quote-object-cost "Quote cost object") | Total cost of the items in the quote. |
| `shipping` | [Cost](https://www.prodigi.com/print-api/docs/reference/#quote-object-cost "Quote cost object") | Total cost of the shipping in the quote. |

### Shipment

| Property | Type | Description |
| --- | --- | --- |
| `carrier` | [Carrier](https://www.prodigi.com/print-api/docs/reference/#quote-object-carrier "Quote carrier object") | The carrier and service. |
| `fulfillmentLocation` | [fulfillmentLocation](https://www.prodigi.com/print-api/docs/reference/#quote-object-fulfillment-location "Quote fulfillment location object") | Country and lab fulfilling the shipment. |
| `cost` | [Cost](https://www.prodigi.com/print-api/docs/reference/#quote-object-cost "Quote cost object") | Cost of the shipment. |
| `items` | array of strings | The [Item](https://www.prodigi.com/print-api/docs/reference/#quote-object-item "Quote item object") IDs that make up the shipment. |

### Carrier

| Property | Type | Description |
| --- | --- | --- |
| `name` | string | The name of the carrier. |
| `service` | string | The name of the carrier service. |

### Fulfillment location

| Property | Type | Description |
| --- | --- | --- |
| `countryCode` | string | The two-letter [ISO country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes "ISO country code list") from where the items will be fulfilled. |
| `labCode` | string | The identifying code of the lab fulfilling the items. |

### Item

The Item object is the same as the request [Item](https://www.prodigi.com/print-api/docs/reference/#create-quote-item) object except it has the addition of an `id` property. This is to help identify the items that belong to each [shipment](https://www.prodigi.com/print-api/docs/reference/#quote-object-shipment "Quote shipment object").

| Property | Type | Description |
| --- | --- | --- |
| `id` | string | ID of the Item, referenced in the shipment object. |
| `sku` | string | Prodigi SKU of the product. Use the [Product Details](https://www.prodigi.com/print-api/docs/reference/#product-details "Product details endpoint") endpoint for full SKU information. |
| `copies` | integer | Number of copies/quantity. |
| `unitCost` | [Cost](https://www.prodigi.com/print-api/docs/reference/#quote-object-cost "Quote cost object") | Cost of each individual item. |
| `attributes` | hashtable | Product attributes, such as a frame colour. The [Product Details](https://www.prodigi.com/print-api/docs/reference/#product-details "Product details endpoint") endpoint returns a SKU's available attributes. |
| `assets` | array of [Assets](https://www.prodigi.com/print-api/docs/reference/#assets "Order asset object") | Expected assets. Some additional assets may incur additional costs. |

### Cost

| Property | Type | Description |
| --- | --- | --- |
| `amount` | string | Cost value. A decimal value as a string. |
| `currency` | string | The [ISO currency code](https://en.wikipedia.org/wiki/ISO_4217 "List of currency codes") of this amount. |

### Issues

The `issues` array contains the details of any order issues.

| Value | Type | Description |
| --- | --- | --- |
| `errorCode` | string | A code that indicates the type the error: \* `destinationCountryCode.UsSalesTaxWarning` A warning that indecates that the prices may be subject to US sales tax. |
| `description` | string | A human-readable description of the error. |

## Create Quote

POST/v4.0/quotes

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/quotes" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '
    {
        "shippingMethod": "Budget",
        "destinationCountryCode": "GB",
        "currencyCode":"GBP",
        "items": [
            {
                "sku": "GLOBAL-CAN-10x10",
                "copies": 5,
                "attributes": { "wrap":"ImageWrap" },
                "assets" : [
                    { "printArea" : "default" }
                ]
            },
            {
                "sku": "GLOBAL-FAP-10x10",
                "copies": 1,
                "attributes": { },
                "assets" : [
                    { "printArea" : "default" }
                ]
            }
        ]
    }
  '
```

Response

Copy to clipboard

```
{
    "outcome": "Created",
    "quotes": [
        {
            "shipmentMethod": "Budget",
            "costSummary": {
                "items": {
                    "amount": "79.35",
                    "currency": "GBP"
                },
                "shipping": {
                    "amount": "19.46",
                    "currency": "GBP"
                }
            },
            "shipments": [
                {
                    "carrier": {
                        "name": "Mixed",
                        "service": "Mixed"
                    },
                    "fulfillmentLocation": {
                        "countryCode": "US",
                        "labCode": "us11"
                    },
                    "cost": {
                        "amount": "17.96",
                        "currency": "GBP"
                    },
                    "items": [
                        "qit_f1c1f62b8fd0486da831c9438e89bc25"
                    ]
                },
                {
                    "carrier": {
                        "name": "royalmail",
                        "service": "Standard"
                    },
                    "fulfillmentLocation": {
                        "countryCode": "GB",
                        "labCode": "uk6"
                    },
                    "cost": {
                        "amount": "1.50",
                        "currency": "GBP"
                    },
                    "items": [
                        "qit_a904222e1c964440870f3400bd2d5973"
                    ]
                }
            ],
            "items": [
                {
                    "id": "qit_f1c1f62b8fd0486da831c9438e89bc25",
                    "sku": "GLOBAL-CAN-10X10",
                    "copies": 5,
                    "unitCost": {
                        "amount": "14.37",
                        "currency": "GBP"
                    },
                    "attributes": {
                        "wrap": "ImageWrap"
                    },
                    "assets": [
                        {
                            "printArea": "default"
                        }
                    ]
                },
                {
                    "id": "qit_a904222e1c964440870f3400bd2d5973",
                    "sku": "GLOBAL-TECH-IP11P-FC-CP",
                    "copies": 1,
                    "unitCost": {
                        "amount": "7.50",
                        "currency": "GBP"
                    },
                    "attributes": {},
                    "assets": [
                        {
                            "printArea": "default"
                        }
                    ]
                }
            ]
        }
    ]
}
```

Requests to the Quote endpoint use a stripped-down structure similar to the [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") object.

### Top level

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| `shippingMethod` | string | no | Your requested shipping method: either `budget`, `standard`, `standardplus`, `express` or `overnight`. |
| `destinationCountryCode` | string | yes | Two-letter [ISO country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes "ISO country code list") country code of the destination country. |
| `currencyCode` | string | no | Three-letter [ISO currency code](https://en.wikipedia.org/wiki/ISO_4217 "List of currency codes"). If not provided, the currency code specified within your merchant settings is used. |
| `items` | array of [Items](https://www.prodigi.com/print-api/docs/reference/#item "Item Obeject") | yes | The items to be quoted. |

### Item

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `sku` | string | yes | Prodigi SKU of the product. The [Product Details](https://www.prodigi.com/print-api/docs/reference/#product-details "Product details endpoint") endpoint returns a SKU's available attributes. |
| `copies` | integer | yes | Number of copies. |
| `attributes` | hashtable | no | Product attributes, such as a frame colour. The [Product Details](https://www.prodigi.com/print-api/docs/reference/#product-details "Product details endpoint") endpoint returns a SKU's available attributes. |
| `assets` | array of [Assets](https://www.prodigi.com/print-api/docs/reference/#create-quote-assets "Quote asset object") | yes | Expected assets. Some assets may incur an additional cost. |

### Assets

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `printArea` | string | yes | Available print areas. |

### Create quote outcomes

In addition to the [General outcomes](https://www.prodigi.com/print-api/docs/reference/#outcomes-general-outcomes "General outcomes"), this endpoint can also return:

| Outcome | Status code | Description |
| --- | --- | --- |
| `created` | 200 | Quote created. |
| `createdWithIssues` | 200 | Quote created but contains issues that should be noted. |

# Product details

The Product Details endpoint returns all available data for a SKU, such as price, attributes, and its required assets and dimensions.

## Product Details object

Product Details Object

Copy to clipboard

```
{
    "sku": "GLOBAL-CAN-10X10",
    "description": "Standard canvas on quality stretcher bar, 25x25cm",
    "productDimensions": {
        "width": 10.0000,
        "height": 10.0000,
        "units": "in"
    },
    "attributes": {
        "wrap": [
            "Black",
            "ImageWrap",
            "MirrorWrap",
            "White"
        ]
    },
    "printAreas": {
        "default": {
            "required": true
        }
    },
    "variants": [
        {
            "attributes": {
                "wrap": "Black"
            },
            "shipsTo": [
                "IM",
                "LU",
                "ID",
                "CI",
                "GR",
                "FK",
                "AL",
                "LA",
                "KY"
            ],
            "printAreaSizes": {
                "default": {
                    "horizontalResolution": 1522,
                    "verticalResolution": 1522
                }
            }
        },
        {
            "attributes": {
                "wrap": "ImageWrap"
            },
            "shipsTo": [
                "IM",
                "LU",
                "ID",
                "CI",
                "GR",
                "FK",
                "AL",
                "LA",
                "KY"
            ],
            "printAreaSizes": {
                "default": {
                    "horizontalResolution": 2137,
                    "verticalResolution": 2137
                }
            }
        },
        {
            "attributes": {
                "wrap": "MirrorWrap"
            },
            "shipsTo": [
                "IM",
                "LU",
                "ID",
                "CI",
                "GR",
                "FK",
                "AL",
                "LA",
                "KY"
            ],
            "printAreaSizes": {
                "default": {
                    "horizontalResolution": 1522,
                    "verticalResolution": 1522
                }
            }
        },
        {
            "attributes": {
                "wrap": "White"
            },
            "shipsTo": [
                "IM",
                "LU",
                "ID",
                "CI",
                "GR",
                "FK",
                "AL",
                "LA",
                "KY"
            ],
            "printAreaSizes": {
                "default": {
                    "horizontalResolution": 1522,
                    "verticalResolution": 1522
                }
            }
        }
    ]
}
```

The Product Details object contains all the information about each product you've requested

### Top level

| Property | Type | Description |
| --- | --- | --- |
| `sku` | string | Our stock-keeping unit identifer for the product. |
| `description` | string | Full name & description of the product. |
| `productDimensions` | [ProductDimensions](https://www.prodigi.com/print-api/docs/reference/#product-details-object-product-dimensions "Product dimensions") | Size of the product. |
| `attributes` | hashtable of [Attributes](https://www.prodigi.com/print-api/docs/reference/#product-details-object-attribute "Product attribute object") | Attributes (name and values) applicable to the product. |
| `print areas` | hashtable of [PrintAreas](https://www.prodigi.com/print-api/docs/reference/#product-details-object-print-area "Product print area object") | Available printable areas for the product. |
| `variants` | array of [Variants](https://www.prodigi.com/print-api/docs/reference/#product-details-object-variant "Variants") | Available variants for the product. |

### Product dimensions

| Property | Type | Description |
| --- | --- | --- |
| `width` | decimal | Width of the product. |
| `height` | decimal | Height of the product. |
| `units` | string | Units of measurement of the `width` and `height`. |

### Attribute

| Property | Type | Description |
| --- | --- | --- |
| `name` | string | Attribute name. e.g. `color`, `mountColor`, `size`, `wrap`, etc. |
| `values` | array of strings | Possible values for this attribute. |

### Print Area

| Property | Type | Description |
| --- | --- | --- |
| `required` | boolean | Whether an asset must be supplied for this print area. |

### Variant

| Property | Type | Description |
| --- | --- | --- |
| `attributes` | hashtable of [Attributes](https://www.prodigi.com/print-api/docs/reference/#product-details-object-attribute "Product attribute object") | The specific attribute name and value for this variant. |
| `shipsTo` | array of strings | an array of country codes |
| `printAreaSizes` | hashtable of [PrintAreaDimensions](https://www.prodigi.com/print-api/docs/reference/#product-details-object-print-area-dimensions "Product print area dimensions") | a dictionary keyed on print area name containing the dimensions for the specific variant |

### Print area dimensions

| Property | Type | Description |
| --- | --- | --- |
| `horizontalResolution` | long | the recommended horizontal size of the print area in pixels |
| `verticalResolution` | long | the recommended vertical size of the print area in pixels |

## Get Product Details

GET/v4.0/products

Copy to clipboard

```
curl "https://api.sandbox.prodigi.com/v4.0/products/GLOBAL-CAN-10x10" \
  -X GET \
  -H "X-API-Key: your-api-key"
```

Response

Copy to clipboard

```
{
    "outcome": "Ok",
    "product": {
        "sku": "GLOBAL-CAN-10X10",
        "description": "Standard canvas on quality stretcher bar, 25x25cm",
        "productDimensions": {
            "width": 10.0000,
            "height": 10.0000,
            "units": "in"
        },
        "attributes": {
            "wrap": [
                "Black",
                "ImageWrap",
                "MirrorWrap",
                "White"
            ]
        },
        "printAreas": {
            "default": {
                "required": true
            }
        },
        "variants": [
            {
                "attributes": {
                    "wrap": "Black"
                },
                "shipsTo": [
                    "IM",
                    "LU",
                    "ID",
                    "CI",
                    "GR",
                    "FK",
                    "AL",
                    "LA",
                    "KY"
                ],
                "printAreaSizes": {
                    "default": {
                        "horizontalResolution": 1522,
                        "verticalResolution": 1522
                    }
                }
            },
            {
                "attributes": {
                    "wrap": "ImageWrap"
                },
                "shipsTo": [
                    "IM",
                    "LU",
                    "ID",
                    "CI",
                    "GR",
                    "FK",
                    "AL",
                    "LA",
                    "KY"
                ],
                "printAreaSizes": {
                    "default": {
                        "horizontalResolution": 2137,
                        "verticalResolution": 2137
                    }
                }
            },
            {
                "attributes": {
                    "wrap": "MirrorWrap"
                },
                "shipsTo": [
                    "IM",
                    "LU",
                    "ID",
                    "CI",
                    "GR",
                    "FK",
                    "AL",
                    "LA",
                    "KY"
                ],
                "printAreaSizes": {
                    "default": {
                        "horizontalResolution": 1522,
                        "verticalResolution": 1522
                    }
                }
            },
            {
                "attributes": {
                    "wrap": "White"
                },
                "shipsTo": [
                    "IM",
                    "LU",
                    "ID",
                    "CI",
                    "GR",
                    "FK",
                    "AL",
                    "LA",
                    "KY"
                ],
                "printAreaSizes": {
                    "default": {
                        "horizontalResolution": 1522,
                        "verticalResolution": 1522
                    }
                }
            }
        ]
    }
}
```

This endpoint returns the [Product Details](https://www.prodigi.com/print-api/docs/reference/#product-details-object "Product details object") for the requested SKU.

## Get photobook spine details

POST/v4.0/products/spine

Copy to clipboard

```
curl "https://api.prodigi.com/v4.0/products/spine" \
  -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '
    {
        "sku": "BOOK-A4-L-HARD-M",
        "destinationCountryCode": "US",
        "state": "CA",
        "numberOfPages": 50
    }
```

Response

Copy to clipboard

```
{
    "success": true,
    "message": "Spine info retrieved (or appropriate error message)",
    "spineInfo": {
        "widthMm": 25.4
    }
}
```

This endpoint returns the required width of the book spine required for a book with the provided number of pages going to a particular destination country.

# Callbacks

Sample callback

Copy to clipboard

```
{
    "specversion": "1.0",
    "type": "com.prodigi.order.status.stage.changed#InProgress",
    "source": "http://api.prodigi.com/v4.0/Orders/",
    "id": "evt_305174",
    "time": "2020-08-14T11:51:01.55Z",
    "datacontenttype": "application/json",
    "data": {
      "order": {
        "id": "ord_1469466",
        "created": "2020-08-14T11:50:54.557Z",
        "status": {
          "stage": "InProgress",
          "issues": [],
          "details": {
            "downloadAssets": "InProgress",
            "printReadyAssetsPrepared": "NotStarted",
            "allocateProductionLocation": "NotStarted",
            "inProduction": "NotStarted",
            "shipping": "NotStarted"
          }
        },
        "charges": [],
        "shipments": [],
        "merchantReference": "1",
        "shippingMethod": "Budget",
        "recipient": {
          "name": "Pwinty Test Order",
          "address": {
            "line1": "123 Test Street",
            "line2": "TESTERTON",
            "postalOrZipCode": "TE5 7IN",
            "countryCode": "US",
            "townOrCity": "TEST CITY",
            "stateOrCounty": "TESTSHIRE"
          },
          "email": "mike.hole@prodigi.com",
          "mobilePhoneNumber": "07987654321"
        },
        "items": [
          {
            "id": "ori_1430070",
            "status": "NotYetDownloaded",
            "sku": "GLOBAL-PHO-12X16-PRO-LUS-UK1",
            "copies": 1,
            "sizing": "fillPrintArea",
            "attributes": {},
            "assets": [
              {
                "id": "ast_116447",
                "status": "InProgress",
                "printArea": "default",
                "url": "https://pwintytest.blob.core.windows.net/sample-media/mike/TestCard.png"
              }
            ],
            "recipientCost": {
              "amount": "543.21",
              "currency": "USD"
            }
          }
        ],
        "packingSlip": {
          "url": "https://pwintytest.blob.core.windows.net/sample-media/mike/PackingSlip.png",
          "status": "NotYetDownloaded"
        }
      }
    },
    "subject": "ord_1469466"
  }
```

We can send callbacks to your chosen endpoint when an order's stage changes or when a shipment is made (see [Status](https://www.prodigi.com/print-api/docs/reference/#status "Status") for details of the Status and Shipments objects).

A callback requires a public url, which can be given globally as a setting in your merchant settings in the [dashboard](https://dashboard.prodigi.com/ "Prodigi dashboard"), or on a per-order basis by setting the `callbackUrl` in the [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") object.

Each callback is in the form of a CloudEvent following the [CloudEvents](https://cloudevents.io/ "CloudEvents") specification.

## Properties

### source `URI-reference`

The `source` identifies the context in which an event happened. This is a URI that points at the host [environment](https://www.prodigi.com/print-api/docs/reference/#environments "Environments") that has produced the callback and the API endpoint that can be used to access the particular source object.

For example for sandbox this would be:

`https://api.sandbox.prodigi.com/v4.0/Orders/`

And the live api:

`https://api.prodigi.com/v4.0/Orders/`

[View the CloudEvents spec ↗](https://github.com/cloudevents/spec/blob/v1.0/spec.md#source-1 "CloudEvents spec for source")

### id `string`

The identifier for the event. Each event ID is unique and starts with the `evt_` prefix.

[View the CloudEvents spec ↗](https://github.com/cloudevents/spec/blob/v1.0/spec.md#id "CloudEvents spec for id")

### type `string`

The `type` property starts with the `com.prodigi` reverse DNS name. This is then followed by the high-level object that is responsible for generating the callback, which in most cases is the [Order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") object followed by the path to the nested object that has changed. Finally, the new value is given as part of a fragment (followed by the `#` character).

For example:

`com.prodigi.order.status.stage.changed#InProgress`

This shows a change to the order stage: the change is to the order status and it has changed to `InProgress`.

[View the CloudEvents spec ↗](https://github.com/cloudevents/spec/blob/v1.0/spec.md#type "CloudEvents spec for type")

Callback Payload

Copy to clipboard

```
"data": {
      "id": "ord_1469466",
      "created": "2020-08-14T11:50:54.557Z",
      "status": {
        "stage": "InProgress"
      }
 }
```

### subject `string`

Used to identify the particular object that produced the callback. In the case of the Prodigi API's callbacks this will be the order id.

### dataContentType `String`

Always `application/json`.

### time `timestamp`

The datetime the event was generated, in [RFC3339 time format](https://tools.ietf.org/html/rfc3339 "RFC3339 time format"). Please note that this time may differ from the actual delivery time of the event because callbacks are queued for delivery.

[View the CloudEvents spec ↗](https://github.com/cloudevents/spec/blob/v1.0/spec.md#time "CloudEvents spec for time")

### specversion `string`

The version of the CloudEvents specification which the event uses. In our case this is version `1.0`.

[View the CloudEvents spec ↗](https://github.com/cloudevents/spec/blob/v1.0/spec.md#specversion "CloudEvents spec for specversion")

### data `json`

Data object of the complete [order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") object at the point the callback was created.

# ID format

To aid parsing, all Prodigi-assigned IDs in the API have a 3-letter prefix according to the object type which it identfies.

| Name | Prefix | Example in v3 | Example in v4 |
| --- | --- | --- | --- |
| Order | `ord_` | `1234567` | `ord_1234567` |
| OrderItem | `ori_` | `1234567` | `ori_1234567` |
| Charge | `chg_` | `345345` | `chg_345345` |
| ChargeItem | `chi_` | `123123` | `chi_123123` |
| Shipment | `shp_` | `456456` | `shp_456456` |
| Asset | `ast_` | `12341234` | `ast_12341234` |

# Outcomes

Outcome & object in a given response

Copy to clipboard

```
{
    "outcome": "Created",
    "order": {
        "id": "ord_840796",
        "created": "2021-03-11T14:31:23.41Z",
        "lastUpdated": "2021-03-11T14:31:23.4931606Z",
        "callbackUrl": null,
        "merchantReference": "MyMerchantReference1",
        "shippingMethod": "Overnight",
        "idempotencyKey": null,
        "status": {
            "stage": "InProgress",
            "issues": [],
            "details": {
                "downloadAssets": "NotStarted",
                "printReadyAssetsPrepared": "NotStarted",
                "allocateProductionLocation": "NotStarted",
                "inProduction": "NotStarted",
                "shipping": "NotStarted"
            }
        },
        "charges": [],
        "shipments": [],
        "recipient": {
            "name": "Mr test",
            "email": null,
            "phoneNumber": null,
            "address": {
                "line1": "14 test place",
                "line2": "test",
                "postalOrZipCode": "12345",
                "countryCode": "US",
                "townOrCity": "somewhere",
                "stateOrCounty": null
            }
        },
        "items": [
            {
                "id": "ori_926886",
                "status": "NotYetDownloaded",
                "merchantReference": "item #1",
                "sku": "GLOBAL-CFPM-16X20",
                "copies": 1,
                "sizing": "fillPrintArea",
                "attributes": {
                    "color": "black"
                },
                "assets": [
                    {
                        "id": "ast_114059",
                        "printArea": "default",
                        "md5Hash": "daa1c811c6038e718a23f0d816914b7b",
                        "url": "https://pwintyimages.blob.core.windows.net/samples/stars/test-sample-grey.png",
                        "status": "InProgress"
                    }
                ],
                "recipientCost": {
                    "amount": "10.74",
                    "currency": "GBP"
                }
            }
        ],
        "packingSlip": null,
        "metadata": {
            "mycustomkey": "some-guid",
            "someCustomerPreference": {
                "preference1": "something",
                "preference2": "red"
            },
            "sourceId": 12345
        }
    },
    "traceParent": "00-65e25206c6b1e34dbdcea1a7051f85bd-f6885faf442b6041-00"
}
```

The `outcome` helps you understand what is happening with your order, and what has happened as a result of each request.

This is especially useful with larger orders, when a change across the whole order (like updating shipping, or cancelling the order) may have impacted your individual shipments.

This field is available on every request.

## General outcomes

The range of returned `outcome` values varies between endpoints, but the general list of possible `outcomes` is as follows

| Outcome | Status code | Description |
| --- | --- | --- |
| `validationFailed` | 400 | We were unable to validate your request. This could be down to incorrect Order ID format, incorrect JSON (fields or malformed) in the body, or missing data. |
| `entityNotFound` | 404 | The endpoint was correct but the API could not find the given entity. |
| `endpointDoesNotExist` | 404 | The API does not recognise the endpoint. |
| `methodNotAllowed` | 405 | Request used an HTTP Method that the endpoint does not support. |
| `invalidContentType` | 415 | The Content-Type header is missing or indicates an unsupported content type. We only accept `application/json`. |
| `internalServerError` | 500 | An unexpected error occurred while processing your request. These are never intentional, so please [let us know](mailto:support@podigi.com "Email support@prodigi.com"). |
| `timedOut` | 500 | We failed to process the request in under a minute and aborted the request. |

# Status

Each order object provided by the API has an associated Status object that provides a rich description of the order's fulfilment process and its current stage.

## Status object

Status object

Copy to clipboard

```
{
    "stage":"InProgress",
    "details" : {
        "downloadAssets":"InProgress",
        "printReadyAssetsPrepared":"NotStarted",
        "allocateProductionLocation ": "NotStarted",
        "inProduction":"NotStarted",
        "shipping":"NotStarted"
    },
    "issues":[
        {
            "objectId": "ori_12345",
            "errorCode" : "items.assets.NotDownloaded",
            "description" : "Warning: Download attempt 1 of 10 failed for 'default' asset on item 'ori_12345' at location 'http://source.url' "
        },
        {
            "objectId": "ord_829398",
            "errorCode": "RequiresPaymentAuthorisation",
            "description": "Payment authorisation required for 'ord_829398' (195.02USD) please use the following URL to make payment: https://beta-dashboard.pwinty.com/payment/97323",
            "authorisationDetails": {
                "authorisationUrl": "https://beta-dashboard.pwinty.com/payment/97323",
                "paymentDetails": {
                    "amount": "195.02",
                    "currency": "USD"
                }
            }
        }
    ]
}
```

### Top level

| Value | Type | Description |
| --- | --- | --- |
| `stage` | string | Current stage the order. |
| `details` | [Details](https://www.prodigi.com/print-api/docs/reference/#status-status-object-details "Details") | The process involved in order production, and the state of each. |
| `issues` | [Issues](https://www.prodigi.com/print-api/docs/reference/#status-status-object-issues "Issues") | Any order issues. |

### Stage

The `stage` description can be one of the following values:

*   `InProgress` The order has been submitted and is now in fulfilment.
*   `Complete` All of the orders shipments have been sent.
*   `Cancelled` The order production has been cancelled.

Please note: an order that has been submitted but is currently paused will not return a status until the pause window has expired and the order is submitted to fulfilment.

### Details

The Details object lists the stages the order goes through during processing, and the status of the order within each of these stages.

| Value | Type | Description |
| --- | --- | --- |
| `downloadAssets` | string | Download of the image assets from your source URLs to Prodigi. |
| `allocateProductionLocation` | string | Allocation of the order items to the most appropriate lab(s). |
| `printReadyAssetsPrepared` | string | Transformation of an asset into a print-ready file for submission to the lab(s). |
| `inProduction` | string | Submission to the lab(s). |
| `shipping` | string | Despatch of the item to the customer |

Each of these `details` stages has one of the following values:

*   `NotStarted` None of the items have been processed for this stage.
*   `InProgress` The process has started. One or more items have been processed but there are some outstanding items.
*   `Complete` All of the items have completed this stage of the process.
*   `Error` There has been an issue with one or more items. Issues will be present within the [Issues](https://www.prodigi.com/print-api/docs/reference/#status-status-object-issues "Issues") collection.

Further details of the production process can be found in the [Process](https://www.prodigi.com/print-api/docs/reference/#the-order-process "Process") section.

### Issues

The `issues` array contains the details of any order issues.

| Value | Type | Description |
| --- | --- | --- |
| `objectId` | string | The object that is in error. This could refer to the order itself (an ID prefixed with `ord_`) or one of the order items (prefixed with `ori_`). |
| `errorCode` | string | A code that indicates the type the error: \* `order.items.assets.NotDownloaded` An asset has failed a download attempt. We attempt to download an asset 10 times. The name of the failed asset is in the error description text. \* `order.items.assets.FailedToDownloaded` An asset failed all 10 download attempts. The name of the failed asset is in the error description text. \* `order.items.ItemUnavailable` A SKU has been marked as currently unavailable. This may be due to a lack of stock and is usually temporary. Customer services will need to be contacted regarding this issue. |
| `description` | string | A human-readable description of the error. |
| `authorisationDetails` | [AuthorisationDetails](https://www.prodigi.com/print-api/docs/reference/#status-status-authorisation-details "Authorisation Details") | If an order requires payment authorization details are provided here. |

### Authorisation Details

| Value | Type | Description |
| --- | --- | --- |
| `authorisationUrl` | string | The url where authorisation of the payment can be carried out. |
| `paymentDetails` | [Cost](https://www.prodigi.com/print-api/docs/reference/#order-object-cost "Cost") | The amount and currency of the required payment. |

# Errors

## Base error object

All errors returned from _authenticated_ requests will have the same basic structure.

Error Response

Copy to clipboard

```
{
    "statusText": "Something went wrong",
    "statusCode": 400,
    "data": {
    },
    "traceParent": "00-2c42dcf1952d634ab2d5d1ab49e8bdf9-c20ae99b6e950049-00"
}
```

| Parameter | Type | Description |
| --- | --- | --- |
| `statusText` | string | Human-readable description of the error. |
| `statusCode` | integer | HTTP status code. |
| `data` | object | JSON object containing additional details about the error where applicable. The structure will depend on the cause of the error. |
| `traceParent` | string | Unique identifier for the request. |

## TraceParent

Every request is assigned a unique identifier which can be used to aid support queries. This identifier is returned as the response header `traceParent` in every request, and is also included in base [Error](https://www.prodigi.com/print-api/docs/reference/#errors-base-error-object "Error object") object for convenience.

## Generic errors

| Error code | Meaning |
| --- | --- |
| `400` | Bad request: the request is malformed in some manner. |
| `401` | Unauthorised: your credentials are missing or incorrect. |
| `404` | Not found: the resource does not exist (or does not exist in your account). |
| `500` | Internal server error: Please [contact support](mailto:support@prodigi.com "Contact us"). |

# The order process

Understanding how we process and fulfill orders will help you understand our API.

Our order process consists of the following steps:

1.  [Order creation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-1-order-creation)
2.  [Assets download](https://www.prodigi.com/print-api/docs/reference/#the-order-process-2-assets-download)
3.  [Lab allocation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-3-lab-allocation)
4.  [Asset preparation](https://www.prodigi.com/print-api/docs/reference/#the-order-process-4-asset-preparation)
5.  [Lab submission](https://www.prodigi.com/print-api/docs/reference/#the-order-process-5-lab-submission)
6.  [Production](https://www.prodigi.com/print-api/docs/reference/#the-order-process-6-production)
7.  [Shipping](https://www.prodigi.com/print-api/docs/reference/#the-order-process-7-shipping)
8.  [Order completion](https://www.prodigi.com/print-api/docs/reference/#the-order-process-8-order-completion)

During the order's lifecycle, we can send you [callbacks](https://www.prodigi.com/print-api/docs/reference/#callbacks "Callbacks") with information on how the order is progressing. We can send callbacks when the following events occur:

*   After the "Create order" stage
*   After the "Shipments made" stage
*   After the "Order completed" stage

1.  Order creation

***

The order is created by POSTing to the `/orders` endpoint. Once any pre-configured pause window has expired, it moves into fulfilment.

*   Order stage: `In progress`
*   Callback available: no

| Task | Stage |
| --- | --- |
| Download assets | `Not started` |
| Print-ready assets prepared | `Not started` |
| Allocate production location | `Not started` |
| In production | `Not started` |
| Shipping | `Not started` |

2.  Assets download

***

We download your assets from your source URIs. We ensure that they are available for processing, and are available should the order need to be resubmitted or checked for quality.

For details of how long we keep the original and transformed images see [image retention](https://www.prodigi.com/print-api/docs/reference/#the-order-process-image-retention "Image retention") below.

*   Order stage: `In progress`
*   Callback available: yes, once complete

| Task | Stage |
| --- | --- |
| Download assets | `In progress` |
| Allocate production location | `Not started` |
| Print-ready assets prepared | `Not started` |
| In production | `Not started` |
| Shipping | `Not started` |

3.  Lab allocation

***

When allocating your order, we allocate to the most cost-effective lab based on the chosen products, destination and shipping method. This may require us to split the order into multiple shipments.

Once this process has been completed, the [order](https://www.prodigi.com/print-api/docs/reference/#order-object "Order object") that is returned by the API shows the allocated [shipments](https://www.prodigi.com/print-api/docs/reference/#order-object-shipment "Shipments") for the order items.

*   Order stage: `In progress`
*   Callback available: no

| Task | Stage |
| --- | --- |
| Download assets | `Complete` |
| Allocate production location | `In progress` |
| Print-ready assets prepared | `Not started` |
| In production | `Not started` |
| Shipping | `Not started` |

4.  Asset preparation

***

We prepare each image asset file according to the requirements of the ordered product/lab (e.g. format or orientation).

*   Order stage: `In progress`
*   Callback available: no

| Task | Stage |
| --- | --- |
| Download assets | `Complete` |
| Allocate production location | `Completed` |
| Print-ready assets prepared | `In progress` |
| In production | `Not started` |
| Shipping | `Not started` |

5.  Lab submission

***

Each shipment is sent to their respective lab.

*   Order stage: `In progress`
*   Callback available: no

| Task | Stage |
| --- | --- |
| Download assets | `Complete` |
| Allocate production location | `Completed` |
| Print-ready assets prepared | `Complete` |
| In production | `In progress` |
| Shipping | `Not started` |

6.  Production

***

Each lab prints the items that they have been allocated.

*   Order stage: `In progress`
*   Callback available: no

| Task | Stage |
| --- | --- |
| Download assets | `Completed` |
| Print-ready assets prepared | `Completed` |
| Allocate production location | `Completed` |
| In production | `In progress` |
| Shipping | `Not started` |

7.  Shipping

***

Once the items are produced, each lab notifies us and provides details of the shipment, including the specific shipping method used and the shipping reference where available.

*   Order stage: `In progress`
*   Callback available: yes, once complete

| Task | Stage |
| --- | --- |
| Download assets | `Completed` |
| Print-ready assets prepared | `Completed` |
| Allocate production location | `Completed` |
| In production | `In progress` |
| Shipping | `In progress` |

8.  Order completion

***

When all items have received a shipping notification the whole order is marked as complete.

*   Order stage: `Complete`
*   Callback available: Yes

| Task | Stage |
| --- | --- |
| Download assets | `Complete` |
| Print-ready assets prepared | `Complete` |
| Allocate production location | `Complete` |
| In production | `Complete` |
| Shipping | `Complete` |

## Image retention

When an order is submitted, we immediately save copies of the order's image assets. We retain these for 30 days, after which they are deleted automatically.

This 30-day period is in case we need to resubmit your order at any point, for example to a different lab.

# Help & support

## Contact

Our API team is always on hand for any support queries — please contact us at [support@prodigi.com](mailto:support@prodigi.com "Email us").

## Guides

*   [Postman collection](https://postman.prodigi.com/ "Prodigi print API Postman collection")
*   [Frequently asked questions](https://www.prodigi.com/faq/print-api/ "API FAQ")
*   [Placing your first order](https://www.prodigi.com/blog/your-first-print-api-order/ "Your first Prodigi API order")
*   [v4 overview](https://www.prodigi.com/blog/announcing-prodigi-print-api-v4/ "An overview of v4 of our API")
*   [Migrating from v3 to v4](https://www.prodigi.com/blog/migrating-from-api-v3-to-v4/ "Migrating to v4 of the Prodigi API")

## Versions

The current version of the API is **v4**.

### Earlier versions

All earlier versions of the API have been discontinued and are no longer available. For guidance on upgrading to v4 please see the [Migration Guide](https://www.prodigi.com/blog/migrating-from-api-v3-to-v4/ "Migrating to v4 of the Prodigi API").

### Changes & breaking changes

We consider a breaking change to be one where we need to remove fields or values. We will not roll out any breaking changes in a given version, instead favouring a minor version increase. We may release additional fields or endpoints without a version bump as we don't consider these breaking changes.