const ProductPreview = ({ productData }) => {
  if (!productData) return null

  const formatPrice = (price, currency) => {
    if (!price) return 'Price not available'
    return `${currency || '$'}${price}`
  }

  const formatRating = (rating, reviewCount) => {
    if (!rating) return null
    return (
      <div className="flex items-center space-x-1">
        <div className="flex text-yellow-400">
          {[...Array(5)].map((_, i) => (
            <svg
              key={i}
              className={`w-4 h-4 ${i < Math.floor(rating) ? 'fill-current' : 'text-gray-300'}`}
              viewBox="0 0 20 20"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          ))}
        </div>
        <span className="text-sm text-gray-600">
          {rating} {reviewCount && `(${reviewCount} reviews)`}
        </span>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
        Product Information
      </h3>
      
      {/* Product Image */}
      {productData.images && productData.images.length > 0 && (
        <div className="mb-4">
          <img
            src={productData.images[0]}
            alt={productData.title}
            className="w-full h-32 object-cover rounded-lg border border-gray-200"
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
        </div>
      )}

      {/* Product Details */}
      <div className="space-y-3">
        <div>
          <h4 className="font-medium text-gray-900 mb-1">{productData.title}</h4>
          {productData.brand && (
            <p className="text-sm text-gray-600">Brand: {productData.brand}</p>
          )}
        </div>

        {productData.price && (
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-green-600">
              {formatPrice(productData.price, productData.currency)}
            </span>
            {productData.availability && (
              <span className={`text-sm px-2 py-1 rounded-full ${
                productData.availability.toLowerCase().includes('stock') ? 
                'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {productData.availability}
              </span>
            )}
          </div>
        )}

        {formatRating(productData.rating, productData.review_count)}

        {productData.category && (
          <p className="text-sm text-gray-600">
            <span className="font-medium">Category:</span> {productData.category}
          </p>
        )}

        {productData.description && (
          <div>
            <p className="text-sm font-medium text-gray-900 mb-1">Description:</p>
            <p className="text-sm text-gray-600 line-clamp-3">
              {productData.description}
            </p>
          </div>
        )}

        {productData.key_features && productData.key_features.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-900 mb-2">Key Features:</p>
            <ul className="text-sm text-gray-600 space-y-1">
              {productData.key_features.slice(0, 3).map((feature, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span>{feature}</span>
                </li>
              ))}
              {productData.key_features.length > 3 && (
                <li className="text-gray-500 italic">
                  +{productData.key_features.length - 3} more features
                </li>
              )}
            </ul>
          </div>
        )}

        {productData.scraped_at && (
          <div className="pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Data scraped: {new Date(productData.scraped_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProductPreview 