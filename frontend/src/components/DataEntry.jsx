import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Save, ChevronLeft, ChevronRight, RefreshCw, FileSpreadsheet } from 'lucide-react'

export default function DataEntry({ user }) {
  const location = useLocation()
  const [sheetId, setSheetId] = useState(location.state?.sheetId || '')
  const [sheetUrl, setSheetUrl] = useState('')
  const [sections, setSections] = useState([])
  const [activeSection, setActiveSection] = useState(0)
  const [sheetData, setSheetData] = useState([])
  const [headers, setHeaders] = useState([])
  const [formData, setFormData] = useState({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchSections()
    if (sheetId) fetchSheetData()
  }, [sheetId])

  const fetchSections = async () => {
    try {
      const response = await fetch('/api/data/sections', { credentials: 'include' })
      if (response.ok) {
        const data = await response.json()
        if (data.length === 0) {
          // Initialize default sections for 73 columns divided into 6 sections
          const defaultSections = [
            { id: 1, section_name: 'Section 1: Basic Info', section_order: 1, columns: Array.from({length: 12}, (_, i) => i) },
            { id: 2, section_name: 'Section 2: Contact Details', section_order: 2, columns: Array.from({length: 12}, (_, i) => i + 12) },
            { id: 3, section_name: 'Section 3: Professional Info', section_order: 3, columns: Array.from({length: 12}, (_, i) => i + 24) },
            { id: 4, section_name: 'Section 4: Financial Data', section_order: 4, columns: Array.from({length: 12}, (_, i) => i + 36) },
            { id: 5, section_name: 'Section 5: Additional Info', section_order: 5, columns: Array.from({length: 12}, (_, i) => i + 48) },
            { id: 6, section_name: 'Section 6: Remarks', section_order: 6, columns: Array.from({length: 13}, (_, i) => i + 60) }
          ]
          setSections(defaultSections)
        } else {
          setSections(data)
        }
      }
    } catch (error) {
      console.error('Failed to fetch sections:', error)
    }
  }

  const fetchSheetData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/sheets/${sheetId}/data?sheet_title=Sheet1`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        if (data.data && data.data.length > 0) {
          setHeaders(data.data[0])
          setSheetData(data.data.slice(1))
        }
      }
    } catch (error) {
      console.error('Failed to fetch sheet data:', error)
    } finally {
      setLoading(false)
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
        const data = await response.json()
        setSheetId(data.sheet_id)
        fetchSheetData()
      } else {
        const error = await response.json()
        alert(error.error || 'Failed to connect sheet')
      }
    } catch (error) {
      alert('Network error')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (columnIndex, value) => {
    setFormData(prev => ({
      ...prev,
      [columnIndex]: value
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const values = headers.map((_, index) => formData[index] || '')
      const response = await fetch(`/api/sheets/${sheetId}/append?sheet_title=Sheet1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ values })
      })
      if (response.ok) {
        alert('Data saved successfully!')
        setFormData({})
        fetchSheetData()
      } else {
        alert('Failed to save data')
      }
    } catch (error) {
      alert('Network error')
    } finally {
      setSaving(false)
    }
  }

  const handleSectionChange = (index) => {
    setActiveSection(index)
  }

  const currentSection = sections[activeSection]
  const currentColumns = currentSection?.columns || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Data Entry</h1>

      {!sheetId ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-4 mb-6">
            <FileSpreadsheet className="h-8 w-8 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Connect Google Sheet</h2>
          </div>
          <form onSubmit={handleConnectSheet} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Google Sheet URL
              </label>
              <input
                type="url"
                value={sheetUrl}
                onChange={(e) => setSheetUrl(e.target.value)}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Connecting...' : 'Connect Sheet'}
            </button>
          </form>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSheetId('')}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <RefreshCw size={20} />
                </button>
                <span className="text-sm text-gray-600">Sheet ID: {sheetId}</span>
              </div>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                <Save size={18} />
                <span>{saving ? 'Saving...' : 'Save Data'}</span>
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Sections</h2>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleSectionChange(Math.max(0, activeSection - 1))}
                    disabled={activeSection === 0}
                    className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50"
                  >
                    <ChevronLeft size={20} />
                  </button>
                  <span className="text-sm text-gray-600">
                    {activeSection + 1} / {sections.length}
                  </span>
                  <button
                    onClick={() => handleSectionChange(Math.min(sections.length - 1, activeSection + 1))}
                    disabled={activeSection === sections.length - 1}
                    className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50"
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 flex space-x-2 overflow-x-auto">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => handleSectionChange(index)}
                  className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap ${
                    activeSection === index
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {section.section_name}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {currentSection?.section_name || 'Select a section'}
              </h2>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="text-center text-gray-500">Loading data...</div>
              ) : headers.length === 0 ? (
                <div className="text-center text-gray-500">
                  No headers found. Make sure the sheet has data in the first row.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {currentColumns.map((colIndex) => (
                    <div key={colIndex}>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {headers[colIndex] || `Column ${colIndex + 1}`}
                      </label>
                      <input
                        type="text"
                        value={formData[colIndex] || ''}
                        onChange={(e) => handleInputChange(colIndex, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
