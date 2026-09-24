import { useState, useEffect } from 'react'
import { Users, ToggleLeft, ToggleRight, Plus, Trash2, Edit, Link as LinkIcon } from 'lucide-react'

export default function AdminPanel({ user }) {
  const [activeTab, setActiveTab] = useState('users')
  const [users, setUsers] = useState([])
  const [features, setFeatures] = useState([])
  const [sections, setSections] = useState([])
  const [sheetUrl, setSheetUrl] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'features') fetchFeatures()
    if (activeTab === 'sections') fetchSections()
  }, [activeTab])

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/admin/users', { credentials: 'include' })
      if (response.ok) setUsers(await response.json())
    } catch (error) {
      console.error('Failed to fetch users:', error)
    }
  }

  const fetchFeatures = async () => {
    try {
      const response = await fetch('/api/admin/features', { credentials: 'include' })
      if (response.ok) setFeatures(await response.json())
    } catch (error) {
      console.error('Failed to fetch features:', error)
    }
  }

  const fetchSections = async () => {
    try {
      const response = await fetch('/api/admin/sections', { credentials: 'include' })
      if (response.ok) setSections(await response.json())
    } catch (error) {
      console.error('Failed to fetch sections:', error)
    }
  }

  const handleConnectSheet = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch('/api/sheets/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ sheet_url: sheetUrl, sheet_name: 'Main Data Sheet' })
      })
      if (response.ok) {
        alert('Sheet connected successfully!')
        setSheetUrl('')
      } else {
        const data = await response.json()
        alert(data.error || 'Failed to connect sheet')
      }
    } catch (error) {
      alert('Network error')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleFeature = async (featureId) => {
    try {
      const response = await fetch(`/api/admin/features/${featureId}/toggle`, {
        method: 'POST',
        credentials: 'include'
      })
      if (response.ok) {
        fetchFeatures()
      }
    } catch (error) {
      console.error('Failed to toggle feature:', error)
    }
  }

  const handleCreateFeature = async () => {
    const name = prompt('Enter feature name:')
    if (!name) return
    const description = prompt('Enter feature description:') || ''
    
    try {
      const response = await fetch('/api/admin/features', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, description, is_enabled: false })
      })
      if (response.ok) fetchFeatures()
    } catch (error) {
      console.error('Failed to create feature:', error)
    }
  }

  const handleDeleteFeature = async (featureId) => {
    if (!confirm('Are you sure you want to delete this feature?')) return
    try {
      const response = await fetch(`/api/admin/features/${featureId}`, {
        method: 'DELETE',
        credentials: 'include'
      })
      if (response.ok) fetchFeatures()
    } catch (error) {
      console.error('Failed to delete feature:', error)
    }
  }

  const handleCreateSection = async () => {
    const name = prompt('Enter section name:')
    if (!name) return
    const order = prompt('Enter section order (1-6):', '1')
    const columns = prompt('Enter column indices (comma-separated, e.g., 0,1,2,3):', '0,1,2')
    
    try {
      const response = await fetch('/api/admin/sections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          section_name: name,
          section_order: parseInt(order),
          columns: columns.split(',').map(c => parseInt(c.trim()))
        })
      })
      if (response.ok) fetchSections()
    } catch (error) {
      console.error('Failed to create section:', error)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Admin Panel</h1>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {['users', 'features', 'sections', 'sheets'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {activeTab === 'users' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Users</h2>
            <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
              <Plus size={16} />
              <span>Add User</span>
            </button>
          </div>
          <div className="p-6">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.username}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.role}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button className="text-blue-600 hover:text-blue-800 mr-3">Edit</button>
                      <button className="text-red-600 hover:text-red-800">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'features' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Features</h2>
            <button
              onClick={handleCreateFeature}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Plus size={16} />
              <span>Add Feature</span>
            </button>
          </div>
          <div className="p-6 space-y-4">
            {features.map((feature) => (
              <div key={feature.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{feature.name}</p>
                  <p className="text-sm text-gray-500">{feature.description}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => handleToggleFeature(feature.id)}
                    className="flex items-center space-x-2"
                  >
                    {feature.is_enabled ? (
                      <ToggleRight className="h-6 w-6 text-green-600" />
                    ) : (
                      <ToggleLeft className="h-6 w-6 text-gray-400" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteFeature(feature.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'sections' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Column Sections</h2>
            <button
              onClick={handleCreateSection}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Plus size={16} />
              <span>Add Section</span>
            </button>
          </div>
          <div className="p-6 space-y-4">
            {sections.map((section) => (
              <div key={section.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-gray-900">{section.section_name}</p>
                  <span className="text-sm text-gray-500">Order: {section.section_order}</span>
                </div>
                <p className="text-sm text-gray-500">Columns: {section.columns.join(', ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'sheets' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Connect Google Sheet</h2>
          </div>
          <div className="p-6">
            <form onSubmit={handleConnectSheet} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Sheet URL
                </label>
                <div className="flex space-x-4">
                  <input
                    type="url"
                    value={sheetUrl}
                    onChange={(e) => setSheetUrl(e.target.value)}
                    placeholder="https://docs.google.com/spreadsheets/d/..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    <LinkIcon size={18} />
                    <span>{loading ? 'Connecting...' : 'Connect'}</span>
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Paste your Google Sheet URL here. Make sure the sheet is shared with your service account.
              </p>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
