import { useState, useEffect } from 'react'
import { Link, FileSpreadsheet, Plus, Users, Settings } from 'lucide-react'

export default function Dashboard({ user }) {
  const [sheets, setSheets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSheets()
  }, [])

  const fetchSheets = async () => {
    try {
      const response = await fetch('/api/sheets/list', { credentials: 'include' })
      if (response.ok) {
        const data = await response.json()
        setSheets(data)
      }
    } catch (error) {
      console.error('Failed to fetch sheets:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Welcome back, {user.username}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center space-x-4">
            <FileSpreadsheet className="h-10 w-10 text-blue-600" />
            <div>
              <p className="text-2xl font-bold text-gray-900">{sheets.length}</p>
              <p className="text-sm text-gray-600">Connected Sheets</p>
            </div>
          </div>
        </div>

        {(user.role === 'admin' || user.role === 'supervisor') && (
          <>
            <Link
              to="/data-entry"
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:border-blue-500 cursor-pointer transition-colors"
            >
              <div className="flex items-center space-x-4">
                <Plus className="h-10 w-10 text-green-600" />
                <div>
                  <p className="text-lg font-bold text-gray-900">Add Data</p>
                  <p className="text-sm text-gray-600">Enter new records</p>
                </div>
              </div>
            </Link>

            <Link
              to="/admin"
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:border-blue-500 cursor-pointer transition-colors"
            >
              <div className="flex items-center space-x-4">
                <Settings className="h-10 w-10 text-purple-600" />
                <div>
                  <p className="text-lg font-bold text-gray-900">Admin Panel</p>
                  <p className="text-sm text-gray-600">Manage users & features</p>
                </div>
              </div>
            </Link>
          </>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Connected Google Sheets</h2>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center text-gray-500">Loading...</div>
          ) : sheets.length === 0 ? (
            <div className="text-center text-gray-500">
              <p>No sheets connected yet.</p>
              {(user.role === 'admin' || user.role === 'supervisor') && (
                <Link to="/admin" className="text-blue-600 hover:underline">
                  Connect a Google Sheet in Admin Panel
                </Link>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {sheets.map((sheet) => (
                <div
                  key={sheet.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{sheet.sheet_name}</p>
                    <p className="text-sm text-gray-500">{sheet.sheet_id}</p>
                  </div>
                  <Link
                    to="/data-entry"
                    state={{ sheetId: sheet.sheet_id }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                  >
                    Open
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
